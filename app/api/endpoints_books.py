from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List
from app.schemas.jobs import JobResponse, JobStatus
from app.core.jobs import JobManager
from app.services.book_processor import BookProcessor
from app.services.storage import StorageService

router = APIRouter()

@router.post("/upload", response_model=JobResponse)
async def upload_book(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    allowed_extensions = ('.txt', '.pdf', '.epub')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only .txt, .pdf, and .epub files are supported")
    
    content = await file.read()
    
    # Create Job
    job = JobManager.create_job(file.filename)
    
    # Start Background Processing
    background_tasks.add_task(BookProcessor.process_book, job.id, content, file.filename)
    
    return job

@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs():
    jobs = JobManager.list_jobs()
    # Convert gs:// URIs to public URLs for frontend
    for job in jobs:
        if job.output_files:
            job.output_files = [
                StorageService.get_public_url(uri) if uri.startswith("gs://") else uri
                for uri in job.output_files
            ]
    return jobs

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Convert gs:// URIs to public URLs for frontend
    if job.output_files:
        job.output_files = [
            StorageService.get_public_url(uri) if uri.startswith("gs://") else uri
            for uri in job.output_files
        ]
    return job

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    success = JobManager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete job")
    
    return {"message": "Job deleted successfully", "id": job_id}
