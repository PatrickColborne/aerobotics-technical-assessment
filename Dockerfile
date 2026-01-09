FROM python:3.12-slim-bookworm

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies (using poetry or pip)
RUN pip install --upgrade pip \
    && pip install fastapi uvicorn[standard] gunicorn httpx # TODO proper dependency management

# Copy the app code
COPY missing_tree_api/app /app

EXPOSE 8000

# Run the application server
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
