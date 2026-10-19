#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="Lume Transcribe.app"
APP_ROOT="$PROJECT_ROOT/dist/$APP_NAME"
RESOURCES="$APP_ROOT/Contents/Resources"
MACOS="$APP_ROOT/Contents/MacOS"
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/lume-transcribe-dist.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT

cd "$PROJECT_ROOT"
npm run build

cp -R dist/. "$STAGING/"

rm -rf "$APP_ROOT"
mkdir -p "$RESOURCES/backend" "$RESOURCES/dist" "$MACOS"
cp -R backend/. "$RESOURCES/backend/"
cp -R "$STAGING"/. "$RESOURCES/dist/"
cp requirements.txt "$RESOURCES/requirements.txt"

cat > "$APP_ROOT/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Lume Transcribe</string>
  <key>CFBundleDisplayName</key><string>Lume Transcribe</string>
  <key>CFBundleIdentifier</key><string>com.lume.transcribe</string>
  <key>CFBundleVersion</key><string>1.0.0</string>
  <key>CFBundleShortVersionString</key><string>1.0.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>LumeTranscribe</string>
  <key>LSUIElement</key><true/>
</dict></plist>
PLIST

cat > "$RESOURCES/run-server.sh" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
APP_RESOURCES="$(cd "$(dirname "$0")/../Resources" && pwd)"
DATA_DIR="$HOME/Library/Application Support/Lume Transcribe"
mkdir -p "$DATA_DIR"
PROJECT_ROOT="$(cd "$APP_RESOURCES/../../../../" && pwd)"
PYTHON_BIN="${LUME_PYTHON:-}"
if [[ -z "$PYTHON_BIN" && -x "$PROJECT_ROOT/.venv/bin/python" ]]; then PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"; fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then PYTHON_BIN="$(command -v python3)"; fi

export PYTHONPATH="$APP_RESOURCES"
export LUME_DATA_DIR="$DATA_DIR"
export WHISPER_MODEL="${WHISPER_MODEL:-base}"
export WHISPER_DEVICE="${WHISPER_DEVICE:-cpu}"
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-int8}"

cd "$APP_RESOURCES"
"$PYTHON_BIN" -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM

for _ in {1..40}; do
  if curl -fsS http://127.0.0.1:8765/api/health >/dev/null 2>&1; then break; fi
  sleep 0.25
done
open "http://127.0.0.1:8765"
wait "$SERVER_PID"
LAUNCHER
chmod +x "$RESOURCES/run-server.sh"
clang -O2 "$PROJECT_ROOT/scripts/macos_launcher.c" -o "$MACOS/LumeTranscribe"

echo "Criado: $APP_ROOT"
