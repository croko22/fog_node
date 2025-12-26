from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobBase(BaseModel):
    filename: str
    total_chunks: int = 0
    processed_chunks: int = 0
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = datetime.now()
    message: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: str
    output_files: List[str] = []

    class Config:
        from_attributes = True
