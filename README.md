# Fog Node TTS

Fog computing node for text-to-speech synthesis using Piper.

## Requirements

- Linux OS
- Python 3.8+
- Piper TTS binary
- ONNX Model file

## Installation

1. Run the setup:
   ```bash
   make setup
   ```

2. Configure environment variables in `.env`:
   - `BUCKET_NAME`: Target Google Cloud Storage bucket
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON
   - `PIPER_BIN_PATH`: Path to piper executable (auto-installed in ./piper/)
   - `MODEL_PATH`: Path to .onnx model (auto-installed)

## Development

- **Run Service:** `make run`
- **Update Dependencies:** `make update-deps` (Compiles requirements.in)
- **Clean Artifacts:** `make clean`

## Usage

The GUI will launch. Click "INICIAR SERVICIO" to start the API and Ngrok tunnel.

## API Endpoints

### Synthesize Audio

**POST** `/api/v1/synthesize`

**Payload:**

```json
{
  "id": "file_identifier",
  "texto": "Text to synthesize"
}
```

**Response:**

```json
{
  "status": "success",
  "file": "file_identifier.wav",
  "node": "Linux-Fog-01"
}
```
