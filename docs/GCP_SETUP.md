# 🌐 Configuración de Google Cloud Platform

Esta guía explica cómo configurar los servicios de GCP necesarios para el proyecto FogNode Audiobooks.

## Prerequisitos

1. Cuenta de Google Cloud Platform
2. `gcloud` CLI instalado: https://cloud.google.com/sdk/docs/install
3. Docker instalado

## Paso 1: Crear proyecto en GCP

```bash
# Autenticarse en GCP
gcloud auth login

# Crear un nuevo proyecto (o usar uno existente)
gcloud projects create tu-proyecto-id --name="FogNode Audiobooks"

# Configurar el proyecto como predeterminado
gcloud config set project tu-proyecto-id

# Habilitar facturación (requerido para algunos servicios)
# Ir a: https://console.cloud.google.com/billing
```

## Paso 2: Habilitar APIs necesarias

```bash
gcloud services enable \
    storage.googleapis.com \
    firestore.googleapis.com
```

## Paso 3: Crear Bucket de Cloud Storage

```bash
# Crear bucket con nombre único (ej: fognode-audiobooks-TIMESTAMP)
BUCKET_NAME="fognode-audiobooks-$(date +%s)"

gcloud storage buckets create gs://$BUCKET_NAME \
    --location=us-central1 \
    --uniform-bucket-level-access

echo "✅ Bucket creado: $BUCKET_NAME"
```

## Paso 4: Crear base de datos Firestore

```bash
gcloud firestore databases create --location=us-central1
```

## Paso 5: Crear Cuenta de Servicio

```bash
PROJECT_ID=$(gcloud config get-value project)
SA_NAME="fognode-service"

# Crear cuenta de servicio
gcloud iam service-accounts create $SA_NAME \
    --display-name="FogNode Service Account"

# Asignar permisos de Storage
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Asignar permisos de Firestore
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

echo "✅ Cuenta de servicio creada"
```

## Paso 6: Generar credenciales JSON

```bash
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts keys create credentials.json \
    --iam-account=$SA_EMAIL

echo "✅ Credenciales guardadas en credentials.json"
```

> ⚠️ **IMPORTANTE**: Nunca subas `credentials.json` a Git. Ya está en `.gitignore`.

## Paso 7: Configurar variables de entorno

Copia `env.template` a `.env` y actualiza los valores:

```bash
cp env.template .env
```

Edita `.env` con tus valores:

```env
# Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
GCP_PROJECT_ID=tu-proyecto-id
BUCKET_NAME=tu-bucket-name
```

## Paso 8: Construir y ejecutar Docker

```bash
# Construir imagen
docker build -t fog_node .

# Ejecutar contenedor
docker run -d \
    --name fog_node \
    -p 8000:8000 \
    fog_node
```

## Verificar configuración

```bash
# Verificar que la API está corriendo
curl http://localhost:8000/api/v1/status

# Debería responder:
# {"status":"online","service":"FogNode Audio","version":"0.1.0"}
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        CLOUD (GCP)                          │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │    Firestore    │         │    Cloud Storage        │   │
│  │  (jobs metadata)│         │  (audio WAV files)      │   │
│  └────────┬────────┘         └────────────┬────────────┘   │
└───────────┼────────────────────────────────┼───────────────┘
            │                                │
            └───────────────┬────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────┐
│                    FOG NODE (Docker)                        │
│                           │                                 │
│   ┌───────────────────────▼─────────────────────────────┐  │
│   │              FastAPI Application                     │  │
│   │  • /api/v1/upload - Recibe PDFs/EPUBs               │  │
│   │  • /api/v1/jobs   - Lista trabajos                  │  │
│   │  • /audio/*       - Sirve archivos de audio         │  │
│   └───────────────────────┬─────────────────────────────┘  │
│                           │                                 │
│   ┌───────────────────────▼─────────────────────────────┐  │
│   │              Piper TTS Engine                        │  │
│   │  • Convierte texto a audio WAV                      │  │
│   │  • Modelo: es_ES-davefx-medium                      │  │
│   └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Costos estimados (Tier gratuito)

| Servicio | Límite gratuito | Uso típico |
|----------|-----------------|------------|
| Firestore | 1 GB almacenamiento, 50K lecturas/día | ✅ Suficiente |
| Cloud Storage | 5 GB almacenamiento | ✅ ~50 audiobooks |

## Troubleshooting

### Error: "Could not automatically determine credentials"
- Verifica que `credentials.json` existe en la raíz del proyecto
- Verifica que `GOOGLE_APPLICATION_CREDENTIALS` apunta al archivo correcto

### Error: "Bucket not found"
- Verifica que el nombre del bucket en `.env` coincide con el creado en GCP
- Verifica que la cuenta de servicio tiene permisos `storage.objectAdmin`

### Error: "Firestore database not found"
- Verifica que creaste la base de datos con `gcloud firestore databases create`
- Verifica que la cuenta de servicio tiene permisos `datastore.user`

## Script de configuración rápida

Para automatizar todo el proceso, ejecuta:

```bash
./scripts/setup_gcp.sh
```

