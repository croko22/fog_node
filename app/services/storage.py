import os
from google.cloud import storage
from app.core.config import settings
from app.core.logger import gui_logger

class StorageService:
    @staticmethod
    def upload_file(file_path: str, destination_blob_name: str) -> str:
        """
        Uploads a file to the bucket.
        Returns the public URL (if public) or the gs:// URI.
        """
        if not settings.BUCKET_NAME:
            gui_logger.log("⚠️ No BUCKET_NAME configured. Skipping upload.")
            return "skipped-no-bucket"

        bucket_name = settings.BUCKET_NAME
        
        gui_logger.log(f"☁️ Subiendo a GCS: {bucket_name}/{destination_blob_name}...")

        try:
            # Initialize client (looks for GOOGLE_APPLICATION_CREDENTIALS env var)
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            blob.upload_from_filename(file_path)

            gui_logger.log(f"✅ Subida exitosa: {destination_blob_name}")
            return f"gs://{bucket_name}/{destination_blob_name}"

        except Exception as e:
            gui_logger.log(f"❌ Error subiendo a Cloud: {str(e)}")
            # No lanzamos excepción para no romper el flujo principal si falla el upload
            # (El audio se generó bien localmente)
            return f"error-upload: {str(e)}"
