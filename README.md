# NoteWise — AI Quiz Generator

A simple React + FastAPI app that turns study documents into multiple-choice quizzes using Gemini and a web research agent. No login or database.

## Start with Docker

1. Install Docker Engine/Desktop with Docker Compose.
2. Copy `.env.example` to `.env` if you do not already have `.env`.
3. Set `GEMINI_API_KEY` in `.env`. The supplied key is already configured locally in this workspace; `.env` is ignored by Git.
4. Run:

   ```sh
   docker compose up --build -d
   ```

5. Open **http://localhost:8080**. Change `PORT` in `.env` if needed.

Check services with `docker compose ps`; view errors with `docker compose logs`; stop with `docker compose down`. Never share the output of `docker compose config` because it expands the API key; use `docker compose config --quiet` to validate configuration.

## Use it

Try `examples/study-notes.pdf` for a ready-to-upload example.

Upload one document, choose 5, 10, or 15 questions and easy/medium/hard difficulty, then generate. A research agent searches Google for related educational information, then a quiz writer creates questions from your notes and the research. Expand Web research on the quiz to see its sources. Answer all questions and check your score. Results include the correct answers and explanations. Retry the same quiz or upload another document.

Supported documents:

- `.pdf`: embedded text, scanned pages, and mixed PDFs. Pages with little readable text use English Tesseract OCR.
- `.docx`: paragraphs and tables.
- `.pptx`: slide text, tables, grouped shapes, and speaker notes.
- `.doc` / `.ppt`: headless LibreOffice converts these to modern Office formats first.

Limits: 10 MB per upload, 80,000 extracted characters. Password-protected files are rejected. OCR quality depends on scan clarity; handwritten notes may not be recognized accurately. Pictures inside Office documents are not OCRed. Export image-only presentations to PDF to use OCR. Two documents can be processed at once; additional requests receive a retry message.

Documents and OCR/conversion output are processed in temporary directories and removed after each request. Extracted notes are sent to Google's Gemini API; the research agent is instructed to search using related topic terms. Google Search grounding must be enabled for your model/account and may incur additional usage charges. Research failures stop generation with a retry message. Quiz state exists only in browser memory, so refreshing clears it. The answer key is returned to the browser: this is a practice tool, not a secure exam system. Cancel stops the browser request; already-started server work may finish and is then cleaned up.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | required | Backend-only API credential |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model with structured output support |
| `PORT` | `8080` | Nginx host port |
| `BIND_ADDRESS` | `127.0.0.1` | Host interface for the frontend |
| `MAX_UPLOAD_MB` | `100` | Backend upload size limit |
| `MAX_TEXT_CHARS` | `80000` | Extracted text limit |
| `OCR_LANGUAGE` | `eng` | Installed Tesseract language |

The last three variables are configured under the backend service in `docker-compose.yml`. If changing upload size, also update `client_max_body_size` in `frontend/nginx.conf` and the frontend validation. Add Tesseract language packages to the backend image before changing `OCR_LANGUAGE`.

The backend Docker image includes Poppler, Tesseract, English OCR data, LibreOffice Writer/Impress, and fonts. Nginx serves the frontend and proxies `/api/` to the internal backend. Only Nginx is exposed. The first image build can take several minutes because Office conversion tools are sizeable. Docker binds the frontend to localhost by default. For the public domain setup, see [deployment instructions](deploy/README.md).

## Local development

Install Python 3.12+, Node 22+, Tesseract, Poppler, and LibreOffice. On Debian/Ubuntu:

```sh
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils libreoffice-writer libreoffice-impress
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/uvicorn app.main:app --app-dir backend --env-file .env --reload
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the Vite URL. Vite forwards API requests to localhost:8000. API documentation: `/api/docs`; health check: `/api/health`.

## Verify

```sh
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
cd frontend && npm run build
```

Extraction integration tests automatically skip OCR and legacy conversion when the system tools are unavailable. Run them in an environment with all document tools installed to cover every format. Most API tests mock Gemini to avoid cost; live generation requires a valid key and available quota.

Gemini integration uses structured JSON output and validates question count, answer choices, and answer indices. Reference: https://ai.google.dev/gemini-api/docs/structured-output

Web research uses a separate search-grounded Gemini call before structured quiz generation. Provider reference: https://ai.google.dev/gemini-api/docs/google-search

Backend logs include request access logs and progress through upload, document extraction, web research, and quiz generation. View them with `docker compose logs -f backend`. Note contents and API keys are not logged.
