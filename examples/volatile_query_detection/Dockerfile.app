FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first to avoid pulling multi-GB CUDA packages
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Pre-bake the embedding model into the image (avoids runtime download)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY demo.py .

CMD ["python", "demo.py"]
