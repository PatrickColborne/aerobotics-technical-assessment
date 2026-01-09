FROM python:3.12-slim-bookworm

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies (using poetry or pip)
RUN pip install --upgrade pip \
    && pip install fastapi uvicorn[standard] gunicorn

# Copy the app code
COPY missing_tree_api /app/missing_tree_api

EXPOSE 8000

# Run the application server
CMD ["gunicorn", "missing_tree_api.app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
