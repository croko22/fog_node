from fastapi import APIRouter, HTTPException
from app.schemas.audio import AudioRequest, AudioResponse
from app.services.piper import PiperService
from app.services.storage import StorageService

router = APIRouter()

@router.post("/synthesize", response_model=AudioResponse)
async def synthesize_audio(request: AudioRequest):
    filename = f"{request.id}.wav"
    
    try:
        # 1. Generar audio localmente
        full_path = PiperService.synthesize(request.texto, filename)
        
        # 2. Subir a Cloud (si está configurado)
        cloud_uri = StorageService.upload_file(full_path, filename)
        
        return AudioResponse(
            status="success",
            file=cloud_uri if "gs://" in cloud_uri else full_path,
            node="Linux-Fog-01"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
