# Build context MUST be the repository root:
#     docker compose build api
#     docker build -f backend/Dockerfile .
#
# This image serves the JSON API only; the website is served by the `frontend`
# service (nginx), so `frontend/` is deliberately not copied here.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/create_admin.py ./create_admin.py
COPY backend/scripts ./scripts

EXPOSE 8000

# No curl in the slim image, so probe /health with the standard library.
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
