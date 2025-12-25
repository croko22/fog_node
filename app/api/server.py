import uvicorn
import contextlib
from fastapi import FastAPI
from pyngrok import ngrok
from app.api.endpoints import router
from app.core.config import settings
from app.core.logger import gui_logger

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    gui_logger.log(f"🚀 API iniciando en puerto {settings.PORT}")
    
    # Iniciar Ngrok si hay token
    try:
        if settings.NGROK_AUTH_TOKEN:
            ngrok.set_auth_token(settings.NGROK_AUTH_TOKEN)
            
            # Limpiar túneles anteriores
            ngrok.kill()
            
            # Crear túnel
            tunnel = ngrok.connect(settings.PORT)
            public_url = tunnel.public_url
            
            gui_logger.log("─" * 30)
            gui_logger.log("🔗 URL PÚBLICA (Headless/Auto):")
            gui_logger.log(f"{public_url}/api/v1/synthesize")
            gui_logger.log("─" * 30)
    except Exception as err:
        gui_logger.log(f"⚠️ Error Ngrok: {err}")
        
    yield
    # SHUTDOWN
    gui_logger.log("🛑 Deteniendo API...")
    ngrok.kill()

def create_app() -> FastAPI:
    app = FastAPI(title="Fog Node TTS", lifespan=lifespan)
    app.include_router(router, prefix="/api/v1")
    return app

api_app = create_app()

def run_server():
    """Function to run the uvicorn server (blocking)."""
    # Usamos settings.PORT
    uvicorn.run(api_app, host="0.0.0.0", port=settings.PORT, log_level="info")
