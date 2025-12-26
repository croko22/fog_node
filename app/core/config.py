import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    PIPER_BIN_PATH = os.getenv("PIPER_BIN_PATH")
    MODEL_PATH = os.getenv("MODEL_PATH")
    PORT = int(os.getenv("PORT", 8000))
    NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
    AUDIO_OUTPUT_DIR = os.getenv("AUDIO_OUTPUT_DIR", "generated_audio")
    USE_CUDA = os.getenv("USE_CUDA", "false").lower() == "true"
    
    # Google Cloud Platform
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    @classmethod
    def validate(cls):
        """Fail fast if critical configuration is missing."""
        if not cls.PIPER_BIN_PATH or not os.path.exists(cls.PIPER_BIN_PATH):
            print(f"❌ ERROR CRÍTICO: No encuentro Piper en: {cls.PIPER_BIN_PATH}")
            print("Revise su archivo .env")
            sys.exit(1)

        if not cls.MODEL_PATH or not os.path.exists(cls.MODEL_PATH):
            print(f"❌ ERROR CRÍTICO: No encuentro el modelo en: {cls.MODEL_PATH}")
            sys.exit(1)

settings = Settings()
