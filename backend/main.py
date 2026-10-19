import json, os, shutil, sqlite3, subprocess, threading, uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.getenv("LUME_DATA_DIR", str(ROOT / "data"))); UPLOADS = DATA / "uploads"; DB_PATH = DATA / "lume.sqlite3"
UPLOADS.mkdir(parents=True, exist_ok=True)
ALLOWED = {"mp4", "mov", "webm", "mkv", "mp3", "wav", "m4a"}
executor = ThreadPoolExecutor(max_workers=1)
db_lock = threading.Lock()
model_lock = threading.Lock()
model_cache = {}
app = FastAPI(title="Lume Transcribe", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False); c.row_factory = sqlite3.Row; return c

with conn() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, filename TEXT, stored_path TEXT, status TEXT, progress REAL DEFAULT 0, language TEXT, duration REAL DEFAULT 0, segments TEXT DEFAULT '[]', error TEXT, created_at TEXT)""")

def get_job(job_id: str):
    with db_lock, conn() as c: return c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()

def public(row):
    if not row: return None
    d = dict(row); d["segments"] = json.loads(d["segments"] or "[]"); return d

def update(job_id, **values):
    if not values: return
    parts = ", ".join(f"{k}=?" for k in values); vals = list(values.values()) + [job_id]
    with db_lock, conn() as c: c.execute(f"UPDATE jobs SET {parts} WHERE id=?", vals)

def media_duration(path: Path) -> float:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, timeout=30)
        return max(0, float(result.stdout.strip()))
    except (ValueError, subprocess.SubprocessError): return 0

def transcribe(job_id: str):
    row = get_job(job_id)
    if not row: return
    path = Path(row["stored_path"])
    try:
        from faster_whisper import WhisperModel
        model_name = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute = os.getenv("WHISPER_COMPUTE_TYPE", "int8" if device == "cpu" else "float16")
        cache_key = (model_name, device, compute)
        if cache_key not in model_cache:
            with model_lock:
                if cache_key not in model_cache:
                    model_cache[cache_key] = WhisperModel(model_name, device=device, compute_type=compute, download_root=str(DATA / "models"))
        model = model_cache[cache_key]
        language = row["language"] if row["language"] and row["language"] != "auto" else None
        segments_iter, info = model.transcribe(str(path), language=language, vad_filter=True, beam_size=5)
        duration = media_duration(path)
        detected = info.language or language or "pt"
        segments = []
        for index, segment in enumerate(segments_iter):
            text = segment.text.strip()
            if text: segments.append({"id": index, "start": round(segment.start, 3), "end": round(segment.end, 3), "text": text})
            progress = min(99, (segment.end / duration * 100) if duration else min(98, index + 1))
            update(job_id, progress=progress)
        update(job_id, status="completed", progress=100, language=detected, duration=duration or (segments[-1]["end"] if segments else 0), segments=json.dumps(segments, ensure_ascii=False))
    except Exception as exc:
        update(job_id, status="failed", error=str(exc)[:1000])

@app.get("/api/health")
def health(): return {"ok": True, "model": os.getenv("WHISPER_MODEL", "base")}

@app.get("/api/jobs")
def jobs():
    with db_lock, conn() as c: rows = c.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [public(r) for r in rows]

@app.post("/api/jobs")
async def create_job(file: UploadFile = File(...), language: str = Form("auto")):
    suffix = Path(file.filename or "").suffix.lower().lstrip(".")
    if suffix not in ALLOWED: raise HTTPException(400, "Formato não suportado. Use MP4, MOV, WEBM, MKV, MP3, WAV ou M4A.")
    job_id = uuid.uuid4().hex; destination = UPLOADS / f"{job_id}.{suffix}"
    size = 0
    with destination.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 2 * 1024 * 1024 * 1024: destination.unlink(missing_ok=True); raise HTTPException(413, "O arquivo excede o limite de 2 GB.")
            output.write(chunk)
    created = datetime.now(timezone.utc).isoformat()
    # O ffprobe é executado no worker; não bloqueia a resposta do upload de vídeos grandes.
    with db_lock, conn() as c: c.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (job_id, file.filename, str(destination), "queued", 0, language, 0, "[]", None, created))
    executor.submit(run_job, job_id)
    return public(get_job(job_id))

def run_job(job_id):
    update(job_id, status="processing", progress=1); transcribe(job_id)

@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    found = get_job(job_id)
    if not found: raise HTTPException(404, "Trabalho não encontrado")
    return public(found)

@app.get("/api/jobs/{job_id}/media")
def media(job_id: str):
    found = get_job(job_id)
    if not found or not Path(found["stored_path"]).exists(): raise HTTPException(404, "Arquivo não encontrado")
    return FileResponse(found["stored_path"], filename=found["filename"])

class SegmentPayload(BaseModel): segments: list[dict[str, Any]]

@app.put("/api/jobs/{job_id}/segments")
def save_segments(job_id: str, payload: SegmentPayload):
    if not get_job(job_id): raise HTTPException(404, "Trabalho não encontrado")
    update(job_id, segments=json.dumps(payload.segments, ensure_ascii=False)); return {"ok": True}

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    found = get_job(job_id)
    if not found: raise HTTPException(404, "Trabalho não encontrado")
    Path(found["stored_path"]).unlink(missing_ok=True)
    with db_lock, conn() as c: c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    return {"ok": True}

def timestamp(seconds: float, comma=False):
    ms = int(round((seconds - int(seconds)) * 1000)); total = int(seconds); h, rem = divmod(total, 3600); m, s = divmod(rem, 60); sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

@app.get("/api/jobs/{job_id}/export/{fmt}")
def export(job_id: str, fmt: str):
    found = get_job(job_id)
    if not found: raise HTTPException(404, "Trabalho não encontrado")
    if fmt not in {"txt", "srt", "vtt"}: raise HTTPException(400, "Formato inválido")
    segments = json.loads(found["segments"] or "[]")
    if fmt == "txt": body = "\n\n".join(s["text"] for s in segments); media = "text/plain; charset=utf-8"
    elif fmt == "srt": body = "\n\n".join(f"{i}\n{timestamp(s['start'], True)} --> {timestamp(s['end'], True)}\n{s['text']}" for i, s in enumerate(segments, 1)); media = "application/x-subrip; charset=utf-8"
    else: body = "WEBVTT\n\n" + "\n\n".join(f"{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text']}" for s in segments); media = "text/vtt; charset=utf-8"
    return Response(body, media_type=media, headers={"Content-Disposition": f'attachment; filename="{Path(found["filename"]).stem}.{fmt}"'})

# Quando existe um build Vite, o mesmo processo também serve a interface para o app macOS.
FRONTEND_DIST = ROOT / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
