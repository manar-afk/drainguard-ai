# Use Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy and install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy pre-compiled frontend distribution files
COPY frontend/dist/ ./frontend/dist/

# Copy startup runner script
COPY run_backend.py .

# Expose default port (Cloud Run dynamically binds to $PORT anyway)
EXPOSE 8000

# Launch server
CMD ["python", "run_backend.py"]
