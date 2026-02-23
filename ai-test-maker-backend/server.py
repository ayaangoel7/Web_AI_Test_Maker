"""
FastAPI Backend for AI Test Maker
=================================

SETUP INSTRUCTIONS:
1. Place this file alongside your existing Python modules (ai_engine.py, pdf_processor.py, etc.)
2. Install dependencies:  pip install fastapi uvicorn python-multipart
3. Run: python server.py
4. The React frontend connects to http://localhost:8000

FOLDER STRUCTURE:
  backend/
  ├── server.py           (this file - FastAPI app)
  ├── ai_engine.py        (your existing file)
  ├── pdf_processor.py    (your existing file)
  ├── test_generator.py   (your existing file)
  ├── test_grader.py      (your existing file)
  ├── question_customizer.py (your existing file)
  ├── models/             (auto-created for AI models)
  └── uploads/            (auto-created for uploaded files)

ENVIRONMENT:
  Create a .env file:
    CORS_ORIGIN=http://localhost:5173
    HOST=0.0.0.0
    PORT=8090

DOCKER (optional):
  docker build -t ai-test-maker-backend .
  docker run -p 8000:8000 --gpus all ai-test-maker-backend

WINDOWS BATCH (run_server.bat):
  @echo off
  cd /d "%~dp0"
  pip install -r requirements.txt
  python server.py

LINUX BASH (run_server.sh):
  #!/bin/bash
  cd "$(dirname "$0")"
  pip install -r requirements.txt
  python server.py
"""

import os
import uuid
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Import your existing modules
from ai_engine import AIEngine
from pdf_processor import PDFProcessor
from test_generator import TestGenerator
from test_grader import TestGrader
from question_customizer import QuestionCustomizer

app = FastAPI(title="AI Test Maker API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ai_engine = AIEngine()
pdf_processor = PDFProcessor()
test_generator = TestGenerator(ai_engine)
test_grader = TestGrader(ai_engine)
question_customizer = QuestionCustomizer()

# Storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
uploaded_files: Dict[str, Path] = {}
processed_content: Dict[str, Any] = {}


# --- Pydantic Models ---
class GenerateRequest(BaseModel):
    file_id: str
    marks: int
    distribution: Dict[str, int]


class GradeRequest(BaseModel):
    test_data: Dict[str, Any]
    answers: Dict[str, str]


# --- Routes ---
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models_loaded": ai_engine.llm is not None,
        "device": ai_engine.device,
    }


@app.get("/models/status")
async def models_status():
    return {
        "exists": ai_engine.models_exist(),
        "loaded": ai_engine.llm is not None,
    }


@app.post("/models/download")
async def download_models():
    async def stream_progress():
        def callback(progress, status=""):
            pass  # Will be handled below

        progress_data = []

        def progress_callback(progress, status=""):
            progress_data.append({"progress": progress, "status": status})

        import threading
        thread = threading.Thread(
            target=ai_engine.download_models_safe,
            args=(progress_callback,),
            daemon=True,
        )
        thread.start()

        while thread.is_alive() or progress_data:
            if progress_data:
                data = progress_data.pop(0)
                yield json.dumps(data) + "\n"
            else:
                await asyncio.sleep(0.5)

    return StreamingResponse(stream_progress(), media_type="application/x-ndjson")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(400, "Only PDF and DOCX files are supported")

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    uploaded_files[file_id] = file_path
    return {"file_id": file_id, "filename": file.filename}


# FIX: Changed from 'async def' to 'def' to run in a thread pool
@app.post("/generate")
def generate_test(request: GenerateRequest):
    file_path = uploaded_files.get(request.file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(404, "File not found. Please upload again.")

    if request.marks not in (10, 25, 50, 100):
        raise HTTPException(400, "Marks must be 10, 25, 50, or 100")

    # Ensure models loaded
    if ai_engine.llm is None:
        try:
            ai_engine.load_models()
        except Exception as e:
            raise HTTPException(500, f"Failed to load models: {e}")

    try:
        # Process file if not cached
        if request.file_id not in processed_content:
            content = pdf_processor.process_file(str(file_path), request.marks)
            processed_content[request.file_id] = content
        else:
            content = processed_content[request.file_id]

        # Generate test
        test_data = test_generator.generate_test_custom(
            content, request.marks, request.distribution
        )

        # Convert to plain dict if needed
        if isinstance(test_data, str):
            test_data = json.loads(test_data)
        elif hasattr(test_data, '__dict__'):
            test_data = test_data.__dict__

        return JSONResponse(content=test_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Test generation failed: {e}")


# FIX: Changed from 'async def' to 'def' to run in a thread pool
@app.post("/grade")
def grade_test(request: GradeRequest):
    if ai_engine.llm is None:
        try:
            ai_engine.load_models()
        except Exception as e:
            raise HTTPException(500, f"Failed to load models: {e}")

    try:
        # Convert string keys to int keys for answers
        int_answers = {int(k): v for k, v in request.answers.items()}

        # Debug: print what's being sent to grader
        print(f"Test data keys: {request.test_data.keys()}")
        print(f"Answers: {int_answers}")

        results = test_grader.grade_test(request.test_data, int_answers)

        # Debug: print what grader returns
        print(f"Grade results type: {type(results)}")

        if isinstance(results, str):
            results = json.loads(results)
        elif hasattr(results, '__dict__'):
            results = results.__dict__

        return JSONResponse(content=results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Grading failed: {e}")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8090"))
    print(f"Starting AI Test Maker API on {host}:{port}")
    print(f"Access from LAN: http://<your-ip>:{port}")
    uvicorn.run(app, host=host, port=port)
