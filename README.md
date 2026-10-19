# Lume Transcribe

Ferramenta local e gratuita para transcrição de áudio e vídeo usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Os arquivos ficam em `data/uploads`, os modelos em `data/models` e o histórico em SQLite; nada é enviado para serviços externos.

## Open source

Este projeto é distribuído sob a licença MIT. Qualquer pessoa pode clonar, estudar, modificar e redistribuir o código conforme os termos da licença.

## Requisitos

- Python 3.10+ (Python 3.11/3.12 é a opção mais previsível para `faster-whisper`)
- Node.js 18+
- FFmpeg (`ffmpeg` e `ffprobe` no PATH)

Em macOS, instale o FFmpeg com `brew install ffmpeg`.

## Instalação e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run dev
```

Se você já tinha instalado as dependências e aparecer `open() got an unexpected keyword argument 'metadata_errors'`, atualize o PyAV no ambiente ativo:

```bash
pip install --force-reinstall "av<19"
```

Abra http://localhost:5173. Na primeira transcrição o modelo escolhido será baixado uma vez para `data/models`. Para uma máquina mais rápida, use `WHISPER_MODEL=small`; para GPU compatível, configure `WHISPER_DEVICE=cuda` e `WHISPER_COMPUTE_TYPE=float16`.

## App para macOS

Depois de instalar as dependências e garantir que o frontend compila:

```bash
chmod +x scripts/build-macos-app.sh
./scripts/build-macos-app.sh
open "dist/Lume Transcribe.app"
```

O app abre `http://127.0.0.1:8765` automaticamente e guarda o histórico, uploads e modelos em `~/Library/Application Support/Lume Transcribe`. Para o primeiro uso, o Python do ambiente ativo precisa ter as dependências de `requirements.txt`; FFmpeg também precisa estar instalado no Mac.

## Clonar em outro computador

```bash
git clone <URL_DO_REPOSITORIO>
cd lume-transcribe
./start.sh
```

Na primeira execução, o modelo Whisper é baixado para o cache local. O download do modelo é a única comunicação externa esperada; os arquivos do usuário permanecem no computador.

## Recursos implementados

Upload drag-and-drop de MP4, MOV, WEBM, MKV, MP3, WAV e M4A; detecção ou seleção manual de idioma; fila em worker; progresso real baseado nos segmentos processados; histórico local; reprodução de mídia; timestamps clicáveis; edição persistida; cópia completa; exportação TXT/SRT/VTT; exclusão de trabalhos e arquivos temporários.

## Verificações

```bash
npm run build
npm run test:backend
```
