#!/bin/bash
# =============================================================================
# Script de configuración automática de GCP para FogNode Audiobooks
# =============================================================================

set -e

echo "🚀 Configuración de GCP para FogNode Audiobooks"
echo "================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI no está instalado${NC}"
    echo "Instálalo desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verificar autenticación
echo "📋 Verificando autenticación en GCP..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}⚠️  No estás autenticado. Iniciando login...${NC}"
    gcloud auth login
fi

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo -e "${GREEN}✅ Autenticado como: $ACCOUNT${NC}"
echo ""

# Obtener o crear proyecto
echo "📋 Proyectos disponibles:"
gcloud projects list --format="table(projectId,name)" 2>/dev/null | head -10
echo ""

read -p "Ingresa el PROJECT_ID a usar (o presiona Enter para crear uno nuevo): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    TIMESTAMP=$(date +%s)
    PROJECT_ID="fognode-audiobooks-${TIMESTAMP:(-6)}"
    echo "Creando proyecto: $PROJECT_ID"
    gcloud projects create $PROJECT_ID --name="FogNode Audiobooks" 2>/dev/null || true
fi

gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Proyecto configurado: $PROJECT_ID${NC}"
echo ""

# Habilitar APIs
echo "📋 Habilitando APIs necesarias..."
gcloud services enable storage.googleapis.com firestore.googleapis.com 2>/dev/null || true
echo -e "${GREEN}✅ APIs habilitadas${NC}"
echo ""

# Crear bucket
BUCKET_NAME="fognode-audiobooks-$(date +%s)"
echo "📋 Creando bucket: $BUCKET_NAME"
gcloud storage buckets create gs://$BUCKET_NAME --location=us-central1 --uniform-bucket-level-access 2>/dev/null || true
echo -e "${GREEN}✅ Bucket creado: $BUCKET_NAME${NC}"
echo ""

# Crear Firestore
echo "📋 Creando base de datos Firestore..."
gcloud firestore databases create --location=us-central1 2>/dev/null || echo "ℹ️  Firestore ya existe"
echo -e "${GREEN}✅ Firestore configurado${NC}"
echo ""

# Crear cuenta de servicio
SA_NAME="fognode-service"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "📋 Creando cuenta de servicio..."
gcloud iam service-accounts create $SA_NAME --display-name="FogNode Service Account" 2>/dev/null || echo "ℹ️  Cuenta ya existe"

echo "📋 Asignando permisos..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin" --quiet 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/datastore.user" --quiet 2>/dev/null || true

echo -e "${GREEN}✅ Cuenta de servicio configurada${NC}"
echo ""

# Generar credenciales
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CREDS_FILE="$PROJECT_ROOT/credentials.json"

echo "📋 Generando credenciales..."
if [ -f "$CREDS_FILE" ]; then
    echo -e "${YELLOW}⚠️  credentials.json ya existe. ¿Sobrescribir? (y/N)${NC}"
    read -r OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Manteniendo credenciales existentes"
    else
        rm "$CREDS_FILE"
        gcloud iam service-accounts keys create "$CREDS_FILE" --iam-account=$SA_EMAIL
    fi
else
    gcloud iam service-accounts keys create "$CREDS_FILE" --iam-account=$SA_EMAIL
fi
echo -e "${GREEN}✅ Credenciales guardadas en: credentials.json${NC}"
echo ""

# Crear archivo .env
ENV_FILE="$PROJECT_ROOT/.env"
echo "📋 Creando archivo .env..."

cat > "$ENV_FILE" << EOF
# Piper TTS Configuration
PIPER_BIN_PATH=/app/bin/piper/piper
MODEL_PATH=/app/models/es_ES-davefx-medium.onnx
AUDIO_OUTPUT_DIR=generated_audio

# Server Configuration
PORT=8000

# Optional: Enable CUDA for GPU acceleration
USE_CUDA=false

# Optional: Ngrok for public URL
NGROK_AUTH_TOKEN=

# Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
GCP_PROJECT_ID=$PROJECT_ID
BUCKET_NAME=$BUCKET_NAME
EOF

echo -e "${GREEN}✅ Archivo .env creado${NC}"
echo ""

# Resumen
echo "=============================================="
echo -e "${GREEN}🎉 ¡Configuración completada!${NC}"
echo "=============================================="
echo ""
echo "Resumen de configuración:"
echo "  • Proyecto GCP:  $PROJECT_ID"
echo "  • Bucket:        $BUCKET_NAME"
echo "  • Firestore:     us-central1"
echo "  • Credenciales:  credentials.json"
echo ""
echo "Próximos pasos:"
echo "  1. docker build -t fog_node ."
echo "  2. docker run -d --name fog_node -p 8000:8000 fog_node"
echo "  3. Abrir http://localhost:8000/api/v1/status"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: No subas credentials.json a Git${NC}"
echo ""

