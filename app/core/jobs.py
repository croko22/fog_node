import uuid
from typing import Dict, List
from app.schemas.jobs import JobResponse, JobStatus

class JobManager:
    _jobs: Dict[str, JobResponse] = {}

    @classmethod
    def create_job(cls, filename: str) -> JobResponse:
        job_id = str(uuid.uuid4())
        job = JobResponse(
            id=job_id,
            filename=filename,
            status=JobStatus.PENDING
        )
        cls._jobs[job_id] = job
        return job

    @classmethod
    def get_job(cls, job_id: str) -> JobResponse:
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
