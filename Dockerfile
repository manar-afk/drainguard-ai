# ==========================================
# STAGE 1: Compile the React Frontend (Using glibc-compatible Node)
# ==========================================
FROM node:18 AS frontend-builder
WORKDIR /app/frontend

# Install dependencies first (for faster cached builds)
COPY frontend/package*.json ./
RUN npm install

# Copy source code and compile React into plain HTML/JS/CSS assets
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Run the Python FastAPI Backend
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Prevent Python from writing pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ ./backend/

# Copy the compiled React assets directly from Stage 1
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

# Copy startup runner script
COPY run_backend.py .

# Expose default port
EXPOSE 8000

# Launch server
CMD ["python", "run_backend.py"]
