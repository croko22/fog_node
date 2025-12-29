import os
from google.cloud import storage
from app.core.config import settings
from app.core.logger import gui_logger
from datetime import timedelta

class StorageService:
    @staticmethod
    def upload_file(file_path: str, destination_blob_name: str) -> str:
        """
        Uploads a file to the bucket.
        Returns the gs:// URI (source of truth for Fog Computing).
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

            # NOTE: ACLs are disabled in Uniform Bucket-Level Access.
            # We skip make_public(). If public access is needed, configure the bucket policy.
            
            gs_uri = f"gs://{bucket_name}/{destination_blob_name}"
            # public_url = blob.public_url # reliant on being public
            
            gui_logger.log(f"✅ Subida exitosa: {destination_blob_name}")
            gui_logger.log(f"   📎 GS URI: {gs_uri}")
            
            return gs_uri

        except Exception as e:
            gui_logger.log(f"❌ Error subiendo a Cloud: {str(e)}")
            # No lanzamos excepción para no romper el flujo principal si falla el upload
            # (El audio se generó bien localmente)
            return f"error-upload: {str(e)}"
    
    @staticmethod
    def get_public_url(gs_uri: str) -> str:
        """
        Converts gs:// URI to public HTTPS URL.
        """
        if not gs_uri.startswith("gs://"):
            return gs_uri  # Already a URL or invalid
        
        try:
            # Extract bucket and blob name from gs:// URI
            parts = gs_uri.replace("gs://", "").split("/", 1)
            if len(parts) != 2:
                return gs_uri
            
            bucket_name, blob_name = parts
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Return public URL
            return blob.public_url
        except Exception as e:
            gui_logger.log(f"⚠️ Error obteniendo URL pública: {str(e)}")
            return gs_uri
    
    @staticmethod
    def get_signed_url(gs_uri: str, expiration_minutes: int = 60) -> str:
        """
        Generates a signed URL for private access (alternative to public URLs).
        """
        if not gs_uri.startswith("gs://"):
            return gs_uri
        
        try:
            parts = gs_uri.replace("gs://", "").split("/", 1)
            if len(parts) != 2:
                return gs_uri
            
            bucket_name, blob_name = parts
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            return url
        except Exception as e:
            gui_logger.log(f"⚠️ Error generando signed URL: {str(e)}")
            return gs_uri
