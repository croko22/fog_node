import os
import io
import asyncio
from app.core.jobs import JobManager, JobStatus
from app.services.piper import PiperService
from app.services.storage import StorageService
import pypdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

class BookProcessor:
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        text = ""
        with io.BytesIO(file_content) as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    @staticmethod
    def extract_text_from_epub(file_content: bytes) -> str:
        # Save bytes to temporary file because ebooklib needs a path
        # Or use BytesIO if library supports it (ebooklib read_epub usually takes path)
        # We'll write to a temp file for safety
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
            
        try:
            book = epub.read_epub(tmp_path)
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text.append(soup.get_text())
            return "\n".join(text)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    async def process_book(job_id: str, file_content: bytes, filename: str):
        """
        Background task to process the uploaded book.
        """
        JobManager.set_status(job_id, JobStatus.PROCESSING, "Reading file...")
        
        try:
            text = ""
            if filename.lower().endswith('.pdf'):
                text = BookProcessor.extract_text_from_pdf(file_content)
            elif filename.lower().endswith('.epub'):
                text = BookProcessor.extract_text_from_epub(file_content)
            else:
                # Default to text
                text = file_content.decode("utf-8")
            
            # Simple chunking by newlines or max chars
            # For better audiobook results, we should split by paragraphs
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            # Group paragraphs into larger chunks (e.g., 25,000 chars ~ 30-40 mins)
            # This reduces the number of files significantly as requested.
            TARGET_CHUNK_SIZE = 25000 
            chunks = []
            current_chunk = ""
            
            for p in paragraphs:
                if len(current_chunk) + len(p) < TARGET_CHUNK_SIZE:
                    current_chunk += "\n" + p
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = p
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            JobManager.update_progress(job_id, 0, len(chunks), "Starting audio generation...")
            
            generated_files = []
            
            for i, chunk in enumerate(chunks):
                if not chunk: continue
                
                chunk_filename = f"{job_id}_part_{i+1:03d}.wav"
                
                # Check status to allow cancellation (future feature)
                
                try:
                    # 1. Generate Audio locally
                    full_path = PiperService.synthesize(chunk, chunk_filename)
                    
                    # 2. Upload to Cloud Storage (if configured) - for backup/persistence
                    cloud_uri = StorageService.upload_file(full_path, f"audiobooks/{job_id}/{chunk_filename}")
                    
                    # Always use local path for output_files (frontend serves from /audio/)
                    # The cloud_uri is for backup/persistence only
                    generated_files.append(full_path)
                    JobManager.add_output_file(job_id, full_path)
                    
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}")
                    # Continue with other chunks or fail hard? 
                    # For now log and continue
                
                JobManager.update_progress(job_id, i + 1)
                # Small yield to not block event loop totally if synchronous
                await asyncio.sleep(0.1) 

            JobManager.set_status(job_id, JobStatus.COMPLETED, "All chunks processed.")
            
        except Exception as e:
            JobManager.set_status(job_id, JobStatus.FAILED, str(e))
