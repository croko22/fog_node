# 🌫️ Fog Node Audiobooks

Nodo de Fog Computing para convertir libros (PDF, EPUB, TXT) a audiobooks usando Piper TTS.

## 🏗️ Arquitectura

```
     ☁️  CLOUD (GCP)                    
    ┌─────────────────────────────────┐  
    │  • Firestore (jobs metadata)    │
    │  • Cloud Storage (audio files)  │
    └───────────────┬─────────────────┘  
                    │
         🌫️  FOG NODE (Este proyecto)
    ┌───────────────┴─────────────────┐  
    │  • FastAPI REST API             │
    │  • Piper TTS Engine             │
    │  • Procesamiento local          │
    └───────────────┬─────────────────┘  
                    │
         📱  EDGE (Frontend/Usuario)
```

## 🚀 Inicio Rápido con Docker

### Opción 1: Solo local (sin GCP)

```bash
# Construir imagen
docker build -t fog_node .

# Ejecutar
docker run -d --name fog_node -p 8000:8000 fog_node

# Verificar
curl http://localhost:8000/api/v1/status
```

### Opción 2: Con GCP (persistencia en la nube)

```bash
# 1. Configurar GCP automáticamente
./scripts/setup_gcp.sh

# 2. Construir imagen
docker build -t fog_node .

# 3. Ejecutar
docker run -d --name fog_node -p 8000:8000 fog_node
```

📖 Ver [docs/GCP_SETUP.md](docs/GCP_SETUP.md) para configuración manual detallada.

## 📋 Requisitos

- Docker (recomendado) o:
  - Linux OS
  - Python 3.11+
  - gcloud CLI (para GCP)

## ⚙️ Configuración

### Variables de entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `PIPER_BIN_PATH` | Ruta al binario de Piper | ✅ |
| `MODEL_PATH` | Ruta al modelo ONNX | ✅ |
| `AUDIO_OUTPUT_DIR` | Directorio de salida | ✅ |
| `GCP_PROJECT_ID` | ID del proyecto GCP | ❌ |
| `BUCKET_NAME` | Nombre del bucket de Cloud Storage | ❌ |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta a credentials.json | ❌ |

### Modos de operación

| Modo | Jobs | Audio | Configuración |
|------|------|-------|---------------|
| **Local** | En memoria | Local | Solo Docker |
| **Cloud** | Firestore | Cloud Storage | + `credentials.json` |

## 🔌 API Endpoints

### Status
```bash
GET /api/v1/status
# {"status":"online","service":"FogNode Audio","version":"0.1.0"}
```

### Upload Book
```bash
POST /api/v1/upload
Content-Type: multipart/form-data

file: <archivo.pdf|.epub|.txt>
```

### List Jobs
```bash
GET /api/v1/jobs
# [{"id":"xxx","filename":"libro.pdf","status":"completed",...}]
```

### Get Job
```bash
GET /api/v1/jobs/{job_id}
```

### Audio Files
```bash
GET /audio/{filename}.wav
```

## 🛠️ Desarrollo Local

```bash
# Instalar dependencias
make setup

# Ejecutar servidor
make run

# Actualizar dependencias
make update-deps

# Limpiar
make clean
```

## 📁 Estructura del Proyecto

```
fog_node/
├── app/
│   ├── api/          # Endpoints REST
│   ├── core/         # Configuración, jobs, logger
│   ├── schemas/      # Modelos Pydantic
│   └── services/     # Piper TTS, Storage, BookProcessor
├── docs/             # Documentación
├── scripts/          # Scripts de utilidad
├── Dockerfile        # Imagen Docker
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🌐 Servicios GCP utilizados

| Servicio | Propósito | Tier Gratuito |
|----------|-----------|---------------|
| **Cloud Storage** | Almacenar archivos WAV | 5 GB |
| **Firestore** | Persistir metadata de jobs | 1 GB, 50K lecturas/día |

## 🐳 Docker Compose

```bash
# Desarrollo
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## 📝 Licencia

MIT License

## 👥 Autores

- Proyecto de Cloud Computing - UNSA
