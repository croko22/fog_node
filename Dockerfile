# Use official Python slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIPER_BIN_PATH=/app/piper/piper \
    MODEL_PATH=/app/model.onnx \
    # Headless mode for Flet/App (though we bypass GUI)
    FLET_FORCE_WEB_SERVER=true

WORKDIR /app

# Install system dependencies
# libasound2 depends on ALSA, needed for some audio tools. 
# libmpv logic handled if needed, but for headless/API usage typically not required for PIPER itself (piper is a binary).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Piper (pinned version matching setup.sh)
RUN curl -L -o piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    && tar -xzf piper.tar.gz \
    && rm piper.tar.gz

# Download Voice Model (ES Davefx Medium)
RUN curl -L -o model.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx \
    && curl -L -o model.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p generated_audio

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Command to run the API directly (headless)
CMD ["uvicorn", "app.api.server:api_app", "--host", "0.0.0.0", "--port", "8000"]
