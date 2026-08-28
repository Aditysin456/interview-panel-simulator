# Use a slim Python base image to keep the container small
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy backend and frontend code into the container
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Cloud Run sets the PORT environment variable (defaults to 8080).
# We tell uvicorn to listen on whatever PORT Cloud Run gives us.
ENV PORT=8080
WORKDIR /app/backend

# Run the FastAPI app with uvicorn, binding to 0.0.0.0 so Cloud Run can reach it
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
