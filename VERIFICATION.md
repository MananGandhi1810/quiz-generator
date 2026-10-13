# Verification

Verified in this workspace on 2026-10-13:

- **24 backend tests passed**, with no skipped tests after making the document tools available. Includes text PDF, scanned PDF through Poppler/Tesseract, DOCX paragraphs/tables, PPTX slides/speaker notes, real DOC/PPT conversion, protected/corrupt/empty files, size/text/page limits, temporary-file cleanup, Gemini errors, malformed results, question count, and answer validation.
- **Frontend production build passed**. npm dependency audit reported zero vulnerabilities.
- **Browser checks passed** at desktop and 390px mobile widths: upload validation, settings, generation, scoring, explanations, retry, no horizontal overflow, and no JavaScript page errors.
- **Live Gemini generation passed** with the supplied key and `gemini-2.5-flash`.
- **Live full flow passed**: PDF upload through Nginx to FastAPI and Gemini, five generated questions displayed in the browser, then correct scoring and explanations.
- **Nginx syntax and proxy routing passed** using the supplied server configuration, with only its port, static-file directory, and backend hostname adapted to local processes.
- **Docker Compose configuration validation passed** (`docker compose config --quiet`). Registry manifests for all three base-image tags were verified.

## Environment limitation

A full `docker compose up --build` run could not be performed: this account lacks access to `/var/run/docker.sock`, sudo requires authentication, and rootless user namespaces are unavailable. The Dockerfiles and Compose configuration are provided and reviewed, but container image builds and container health checks remain unverified here. Run the Docker startup command in README.md on an account with Docker access.

The host also lacks installed OCR/Office tools. For integration testing only, packages were downloaded and extracted into temporary directories; no system installation was made. One Starlette TestClient deprecation warning was emitted; all tests passed.

Browser screenshots are in the ignored `artifacts/` directory. A sample PDF is in `examples/`.
