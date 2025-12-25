import os
import subprocess
from app.core.config import settings
from app.core.logger import gui_logger

class PiperService:
    @staticmethod
    def synthesize(text: str, filename: str):
        # Asegurar directorio de salida
        output_dir = settings.AUDIO_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        gui_logger.log(f"📥 Procesando: {text[:30]}...")
        
        # Comando seguro (usamos shell=True por el pipe localmente)
        cmd = f'echo "{text}" | {settings.PIPER_BIN_PATH} --model {settings.MODEL_PATH} --output_file "{output_path}"'
        
        try:
            # En entorno de producción real, evitar shell=True si es posible o sanitizar rigurosamente.
            # Aquí asumimos entorno controlado.
            subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
            
            gui_logger.log(f"✅ Audio generado: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error en Piper: {str(e)}"
            gui_logger.log(f"❌ {error_msg}")
            raise Exception(error_msg)
