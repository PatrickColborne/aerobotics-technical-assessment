# Use slim Python image
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip \
    && pip install gunicorn uvicorn[standard]

# Copy pyproject.toml
COPY pyproject.toml /app/

# Copy the actual package
COPY src /app/src

# Install the package (runtime dependencies only)
RUN pip install .

# Expose the FastAPI port
EXPOSE 8000

# Use environment variables for API key and base URL
ENV AEROBOTICS_API_KEY=""
ENV AEROBOTICS_BASE_URL="https://api.aerobotics.com"

# Run Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "missing_tree_api.app.main:app", "--bind", "0.0.0.0:8000"]