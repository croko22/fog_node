#!/bin/bash
set -e

echo "Initializing Fog Node environment..."

# 1. System Dependencies (Libmpv fix)
echo "Checking system dependencies..."
if ! ldconfig -p | grep -q libmpv.so.1; then
    echo "⚠️  libmpv.so.1 not found. Attempting fix..."
    if [ -f /usr/lib/libmpv.so ]; then
        echo "Creating symlink for libmpv.so -> libmpv.so.1 (Requires sudo)"
        sudo ln -s /usr/lib/libmpv.so /usr/lib/libmpv.so.1
        echo "✅ Fixed libmpv symlink."
    elif [ -f /usr/lib/x86_64-linux-gnu/libmpv.so ]; then
         echo "Creating symlink for libmpv.so -> libmpv.so.1 (Requires sudo)"
         sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1
         echo "✅ Fixed libmpv symlink."
    else
        echo "❌ libmpv.so not found. Please install libmpv-dev or mpv."
        echo "Ubuntu/Debian: sudo apt install libmpv-dev"
        echo "Arch: sudo pacman -S mpv"
    fi
else
    echo "✅ libmpv.so.1 found."
fi

# 2. Virtual Environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Piper Setup
if [ ! -f "piper/piper" ]; then
    echo "Downloading Piper..."
    # Download Piper (Linux x86_64) - pinned version for stability
    wget -O piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
    tar -xzf piper.tar.gz
    rm piper.tar.gz
    echo "✅ Piper downloaded and extracted."
else
    echo "✅ Piper binary already exists."
fi

# 4. Voice Model Download
MODEL_NAME="es_ES-davefx-medium"
if [ ! -f "${MODEL_NAME}.onnx" ]; then
    echo "Downloading Voice Model (${MODEL_NAME})..."
    wget -O ${MODEL_NAME}.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/${MODEL_NAME}.onnx
    wget -O ${MODEL_NAME}.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/${MODEL_NAME}.onnx.json
    echo "✅ Voice model downloaded."
else
    echo "✅ Voice model already exists."
fi

# 5. Configuration (.env)
echo "Configuring .env..."
cat <<EOT > .env
# Configuración del Servidor
PORT=8000
ENV_MODE=development

# Configuración de Piper (Rutas relativas o absolutas)
# En Linux suele ser ./piper/piper si descomprimió ahí
PIPER_BIN_PATH=$(pwd)/piper/piper
MODEL_PATH=$(pwd)/${MODEL_NAME}.onnx

# Ngrok
NGROK_AUTH_TOKEN=37LEi6vKPfpg591O9V763FkXlQE_5E3SWxoXchMdvJttvz4mV

# Google Cloud Storage
BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=
EOT

echo "✅ Setup complete. You can now run ./run.sh"
