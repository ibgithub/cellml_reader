FROM python:3.12-slim

# Install system dependencies (including Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
