FROM python:3.10-slim

# Install system dependencies if PyMuPDF requires any (slim might need basic libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements and install
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application files
COPY . .

# Hugging Face Spaces / default container port is 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
