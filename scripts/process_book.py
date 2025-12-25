import os
import argparse
import requests
import json
import time
from tqdm import tqdm
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/v1/synthesize"
OUTPUT_DIR = Path("generated_audio/books")

def clean_text(text: str) -> str:
    """Basic text cleanup."""
    return text.strip().replace("\n", " ")

def split_text(text: str, max_chars=500) -> list[str]:
    """Split text into chunks suitable for TTS."""
    # This is a naive splitter. For production, use NLTK or similar.
    chunks = []
    current_chunk = ""
    
    sentences = text.replace(".", ".|").replace("?", "?|").replace("!", "!|").split("|")
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return [c for c in chunks if c.strip()]

def process_book(input_file: Path, book_id: str):
    """Orchestrate the conversion."""
    print(f"📖 Reading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        full_text = f.read()

    chunks = split_text(full_text)
    print(f"🧩 Split into {len(chunks)} chunks.")
    
    book_dir = OUTPUT_DIR / book_id
    book_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for i, chunk in enumerate(tqdm(chunks, desc="Synthesizing")):
        chunk_id = f"{book_id}_part_{i:04d}"
        payload = {
            "id": chunk_id,
            "texto": chunk
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            results.append(data)
            
            # Optional: Sleep to imply 'network latency' or avoid spamming
            # time.sleep(0.1) 
            
        except Exception as e:
            print(f"❌ Error on chunk {i}: {e}")
            
    # Combine Report
    report_file = book_dir / "report.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"✅ Audiobook generation complete! Check {book_dir}")
    print(f"📄 Report saved to {report_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fog Node Audiobook Orchestrator")
    parser.add_argument("--input", required=True, help="Path to text file")
    parser.add_argument("--id", required=True, help="Unique ID for the book")
    
    args = parser.parse_args()
    process_book(Path(args.input), args.id)
