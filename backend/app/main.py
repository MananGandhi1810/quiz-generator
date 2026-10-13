import asyncio
import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool
from .documents import DocumentError, SUPPORTED, extract_document
from .gemini import GeminiError, generate_quiz

app = FastAPI(title='Study Notes Quiz API', docs_url='/api/docs', openapi_url='/api/openapi.json')
MAX_UPLOAD = int(os.getenv('MAX_UPLOAD_MB', '10')) * 1024 * 1024
processing = asyncio.Semaphore(2)


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'gemini_configured': bool(os.getenv('GEMINI_API_KEY'))}


@app.post('/api/quiz')
async def quiz(file: UploadFile = File(...), question_count: int = Form(10), difficulty: Literal['easy', 'medium', 'hard'] = Form('medium')):
    try:
        if question_count not in (5, 10, 15):
            raise HTTPException(422, 'Choose 5, 10, or 15 questions.')
        suffix = Path(file.filename or '').suffix.lower()
        if suffix not in SUPPORTED:
            raise HTTPException(415, 'Upload a PDF, Word, or PowerPoint document.')
        if processing.locked():
            raise HTTPException(503, 'The server is processing other notes. Please try again shortly.')
        async with processing:
            with tempfile.TemporaryDirectory(prefix='study-quiz-') as directory:
                path = Path(directory) / ('notes' + suffix)
                size = 0
                with path.open('wb') as target:
                    while chunk := await file.read(64 * 1024):
                        size += len(chunk)
                        if size > MAX_UPLOAD:
                            raise HTTPException(413, f'Upload a file smaller than {MAX_UPLOAD // 1024 // 1024} MB.')
                        target.write(chunk)
                text, ocr_pages = await run_in_threadpool(extract_document, path)
                result = await generate_quiz(text, question_count, difficulty)
                return {**result.model_dump(), 'source': {'filename': file.filename, 'ocr_pages': ocr_pages}, 'difficulty': difficulty}
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from None
    except GeminiError as exc:
        raise HTTPException(exc.status, str(exc)) from None
    finally:
        await file.close()
