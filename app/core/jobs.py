import uuid
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.schemas.jobs import JobResponse, JobStatus
from app.core.logger import gui_logger

# Try to import Firestore, fallback to in-memory if not available
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    gui_logger.log("⚠️ Firestore not available, using in-memory storage")


class FirestoreJobManager:
    """Job manager that persists jobs to Firestore."""
    
    COLLECTION_NAME = "audiobook_jobs"
    
    def __init__(self):
        self.db = firestore.Client()
        self.collection = self.db.collection(self.COLLECTION_NAME)
    
    def _job_to_dict(self, job: JobResponse) -> dict:
        return {
            "id": job.id,
            "filename": job.filename,
            "status": job.status.value,
            "total_chunks": job.total_chunks,
            "processed_chunks": job.processed_chunks,
            "message": job.message,
            "output_files": job.output_files,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
    
    def _dict_to_job(self, data: dict) -> JobResponse:
        return JobResponse(
            id=data.get("id"),
            filename=data.get("filename", ""),
            status=JobStatus(data.get("status", "pending")),
            total_chunks=data.get("total_chunks", 0),
            processed_chunks=data.get("processed_chunks", 0),
            message=data.get("message"),
            output_files=data.get("output_files", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )
    
    def create_job(self, filename: str) -> JobResponse:
        job_id = str(uuid.uuid4())
        job = JobResponse(
            id=job_id,
            filename=filename,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self.collection.document(job_id).set(self._job_to_dict(job))
        gui_logger.log(f"📝 Job creado en Firestore: {job_id}")
        return job
    
    def get_job(self, job_id: str) -> Optional[JobResponse]:
        doc = self.collection.document(job_id).get()
        if doc.exists:
            return self._dict_to_job(doc.to_dict())
        return None
    
    def list_jobs(self) -> List[JobResponse]:
        docs = self.collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
        return [self._dict_to_job(doc.to_dict()) for doc in docs]
    
    def update_progress(self, job_id: str, processed_chunks: int, total_chunks: int = None, message: str = None):
        updates = {"processed_chunks": processed_chunks}
        if total_chunks is not None:
            updates["total_chunks"] = total_chunks
        if message:
            updates["message"] = message
        self.collection.document(job_id).update(updates)
    
    def set_status(self, job_id: str, status: JobStatus, message: str = None):
        updates = {"status": status.value}
        if message:
            updates["message"] = message
        self.collection.document(job_id).update(updates)
    
    def add_output_file(self, job_id: str, file_path: str):
        self.collection.document(job_id).update({
            "output_files": firestore.ArrayUnion([file_path])
        })
    
    def delete_job(self, job_id: str) -> bool:
        try:
            self.collection.document(job_id).delete()
            gui_logger.log(f"🗑️ Job eliminado de Firestore: {job_id}")
            return True
        except Exception as e:
            gui_logger.log(f"❌ Error eliminando job: {e}")
            return False


class InMemoryJobManager:
    """Fallback job manager that stores jobs in memory."""
    
    _jobs: Dict[str, JobResponse] = {}

    @classmethod
    def create_job(cls, filename: str) -> JobResponse:
        job_id = str(uuid.uuid4())
        job = JobResponse(
            id=job_id,
            filename=filename,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        cls._jobs[job_id] = job
        return job

    @classmethod
    def get_job(cls, job_id: str) -> Optional[JobResponse]:
        return cls._jobs.get(job_id)

    @classmethod
    def list_jobs(cls) -> List[JobResponse]:
        return list(cls._jobs.values())

    @classmethod
    def update_progress(cls, job_id: str, processed_chunks: int, total_chunks: int = None, message: str = None):
        if job_id in cls._jobs:
            if total_chunks:
                cls._jobs[job_id].total_chunks = total_chunks
            cls._jobs[job_id].processed_chunks = processed_chunks
            if message:
                cls._jobs[job_id].message = message

    @classmethod
    def set_status(cls, job_id: str, status: JobStatus, message: str = None):
        if job_id in cls._jobs:
            cls._jobs[job_id].status = status
            if message:
                cls._jobs[job_id].message = message

    @classmethod
    def add_output_file(cls, job_id: str, file_path: str):
         if job_id in cls._jobs:
            cls._jobs[job_id].output_files.append(file_path)

    @classmethod
    def delete_job(cls, job_id: str) -> bool:
        if job_id in cls._jobs:
            del cls._jobs[job_id]
            return True
        return False


# Choose the appropriate job manager based on availability and configuration
def _get_job_manager():
    """Factory function to get the appropriate job manager."""
    if FIRESTORE_AVAILABLE and os.getenv("GCP_PROJECT_ID"):
        try:
            manager = FirestoreJobManager()
            gui_logger.log("✅ Usando Firestore para persistencia de jobs")
            return manager
        except Exception as e:
            gui_logger.log(f"⚠️ Error inicializando Firestore: {e}")
            gui_logger.log("⚠️ Usando almacenamiento en memoria")
    return InMemoryJobManager()


# Global job manager instance
_job_manager = None

def get_job_manager():
    global _job_manager
    if _job_manager is None:
        _job_manager = _get_job_manager()
    return _job_manager


# Backwards-compatible class that delegates to the appropriate manager
class JobManager:
    @classmethod
    def create_job(cls, filename: str) -> JobResponse:
        return get_job_manager().create_job(filename)

    @classmethod
    def get_job(cls, job_id: str) -> Optional[JobResponse]:
        return get_job_manager().get_job(job_id)

    @classmethod
    def list_jobs(cls) -> List[JobResponse]:
        return get_job_manager().list_jobs()

    @classmethod
    def update_progress(cls, job_id: str, processed_chunks: int, total_chunks: int = None, message: str = None):
        return get_job_manager().update_progress(job_id, processed_chunks, total_chunks, message)

    @classmethod
    def set_status(cls, job_id: str, status: JobStatus, message: str = None):
        return get_job_manager().set_status(job_id, status, message)

    @classmethod
    def add_output_file(cls, job_id: str, file_path: str):
        return get_job_manager().add_output_file(job_id, file_path)

    @classmethod
    def delete_job(cls, job_id: str) -> bool:
        return get_job_manager().delete_job(job_id)
