# Guia de replicação

Este guia permite que outra pessoa clone o Lume Transcribe e execute uma cópia local do projeto.

## 1. Pré-requisitos

Instale:

- Git
- Node.js 18+
- Python 3.10+
- FFmpeg e FFprobe

No macOS:

```bash
brew install git node python ffmpeg
```

No Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv nodejs npm ffmpeg
```

## 2. Clonar e iniciar

```bash
git clone https://github.com/MarquinhoAmorim/lume-transcribe.git
cd lume-transcribe
./start.sh
```

Abra `http://localhost:5173`.

O script cria o ambiente Python, instala as dependências e inicia frontend e backend.

## 3. Configuração opcional

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Variáveis disponíveis:

| Variável | Padrão | Uso |
| --- | --- | --- |
| `WHISPER_MODEL` | `base` | Modelo local do Whisper |
| `WHISPER_DEVICE` | `cpu` | `cpu` ou `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | Tipo de computação |
| `LUME_DATA_DIR` | `./data` | Pasta de uploads, modelos e banco |

Modelos comuns:

| Modelo | Qualidade | Velocidade | Indicação |
| --- | --- | --- | --- |
| `tiny` | básica | muito alta | testes rápidos |
| `base` | boa | alta | padrão recomendado |
| `small` | melhor | média | máquinas mais potentes |
| `medium` | alta | baixa | maior precisão |

Exemplo:

```bash
WHISPER_MODEL=small npm run dev
```

## 4. Validar a instalação

Em outro terminal, execute:

```bash
npm run build
npm run test:backend
curl http://localhost:8000/api/health
```

O último comando deve retornar um status de saúde da API.

## 5. Dados locais

Os dados não entram no Git:

```text
data/uploads/   arquivos enviados
data/models/    modelos Whisper baixados
data/*.sqlite3  histórico local
```

Para começar de novo, pare o servidor e remova apenas a pasta `data/`. Isso apaga uploads, modelos e histórico locais.

## 6. Empacotar para macOS

```bash
./scripts/build-macos-app.sh
open "dist/Lume Transcribe.app"
```

O aplicativo usa o servidor local e salva os dados em `~/Library/Application Support/Lume Transcribe`.

## 7. Fluxo de contribuição

```bash
git checkout -b feature/minha-melhoria
npm run build
npm run test:backend
git add .
git commit -m "feat: descreva a mudança"
git push origin feature/minha-melhoria
```

Depois, abra um Pull Request descrevendo o problema, a solução e como você validou a alteração.
