FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the fastembed model into the image so the first request doesn't pay download cost.
# This is a ~70 MB ONNX model (BAAI/bge-small-en-v1.5, 384-dim).
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

# Copy source
COPY . .

# Do NOT build the RAG index here — Redis is not available at image-build time.
# The startup hook in src/api.py builds the index in-process on first boot.

EXPOSE 8000

CMD uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}
