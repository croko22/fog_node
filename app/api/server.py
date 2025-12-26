import uvicorn
import contextlib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from app.api.endpoints import router as audio_router
from app.api.endpoints_books import router as books_router
from app.core.config import settings
from app.core.logger import gui_logger
from fastapi.staticfiles import StaticFiles
import os

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    gui_logger.log(f"API starting on port {settings.PORT}")
    try:
        if settings.NGROK_AUTH_TOKEN:
            ngrok.set_auth_token(settings.NGROK_AUTH_TOKEN)
            ngrok.kill()
            tunnel = ngrok.connect(settings.PORT)
            public_url = tunnel.public_url
            gui_logger.log("-" * 30)
            gui_logger.log("PUBLIC URL")
            gui_logger.log(f"{public_url}/api/v1/synthesize")
            gui_logger.log("-" * 30)
    except Exception as err:
        gui_logger.log(f"Ngrok error: {err}")
    yield
    gui_logger.log("Stopping API")
    ngrok.kill()

def create_app() -> FastAPI:
    app = FastAPI(title="Fog Node TTS", lifespan=lifespan)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Prevent crash when validation error involves binary data that can't be decoded
        try:
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors(), "body": "Invalid body content"},
            )
        except Exception:
            return JSONResponse(
                status_code=422,
                content={"detail": "Validation error (binary data likely sent to JSON endpoint)"},
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(audio_router, prefix="/api/v1")
    app.include_router(books_router, prefix="/api/v1", tags=["books"])
    os.makedirs(settings.AUDIO_OUTPUT_DIR, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=settings.AUDIO_OUTPUT_DIR), name="audio")
    return app

api_app = create_app()

def run_server():
    uvicorn.run(api_app, host="0.0.0.0", port=settings.PORT, log_level="info")
