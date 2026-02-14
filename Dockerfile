FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py .
COPY index.html .

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Run the server
CMD ["python", "server.py"]
