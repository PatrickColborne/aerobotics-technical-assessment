# Missing Trees Detection API

A Python REST API application for detecting missing trees in orchards based on expected grid patterns.

## Overview

This application provides an API endpoint that analyzes tree positions in an orchard and identifies locations where trees are expected but missing. It uses grid pattern detection to automatically identify the orchard layout and find gaps.

## Features

- **Automatic Grid Detection**: Automatically detects row/column spacing and grid dimensions from existing tree positions
- **Manual Grid Parameters**: Supports explicit grid parameters for known orchard layouts
- **REST API**: Easy-to-use REST API with JSON input/output
- **Docker Support**: Fully containerized for easy deployment to cloud providers
- **Comprehensive Testing**: Unit and integration tests included

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the API.

### Detect Missing Trees
```
POST /detect-missing-trees
```

**Request Body:**
```json
{
  "tree_positions": [
    {"x": 0, "y": 0},
    {"x": 5, "y": 0},
    {"x": 10, "y": 0}
  ],
  "expected_rows": 3,
  "expected_cols": 3,
  "row_spacing": 5.0,
  "col_spacing": 5.0
}
```

Optional parameters (auto-detected if not provided):
- `expected_rows`: Number of rows in the orchard grid
- `expected_cols`: Number of columns in the orchard grid
- `row_spacing`: Distance between rows in meters
- `col_spacing`: Distance between columns in meters

**Response:**
```json
{
  "missing_trees": [
    {"x": 0, "y": 5},
    {"x": 5, "y": 5}
  ],
  "total_missing": 2
}
```

## Installation and Usage

### Running Locally with Python

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Access the API at `http://localhost:8000`

4. View interactive API documentation at `http://localhost:8000/docs`

### Running with Docker

1. Build the Docker image:
```bash
docker build -t missing-trees-api .
```

2. Run the container:
```bash
docker run -p 8000:8000 missing-trees-api
```

3. Access the API at `http://localhost:8000`

### Running Tests

```bash
pytest
```

Or for verbose output:
```bash
pytest -v
```

## Example Usage

### Using curl:
```bash
curl -X POST "http://localhost:8000/detect-missing-trees" \
  -H "Content-Type: application/json" \
  -d '{
    "tree_positions": [
      {"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 10, "y": 0},
      {"x": 0, "y": 5}, {"x": 10, "y": 5},
      {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 10, "y": 10}
    ]
  }'
```

### Using Python requests:
```python
import requests

response = requests.post(
    "http://localhost:8000/detect-missing-trees",
    json={
        "tree_positions": [
            {"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 10, "y": 0},
            {"x": 0, "y": 5}, {"x": 10, "y": 5},
            {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 10, "y": 10}
        ]
    }
)

print(response.json())
```

## Deployment to Cloud Providers

The Docker image can be deployed to various cloud providers:

### AWS (ECS/ECR)
```bash
# Tag and push to ECR
docker tag missing-trees-api:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/missing-trees-api:latest
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/missing-trees-api:latest
```

### Google Cloud Platform (Cloud Run)
```bash
# Tag and push to GCR
docker tag missing-trees-api:latest gcr.io/<project-id>/missing-trees-api:latest
docker push gcr.io/<project-id>/missing-trees-api:latest
```

### Azure (Container Instances)
```bash
# Tag and push to ACR
docker tag missing-trees-api:latest <registry-name>.azurecr.io/missing-trees-api:latest
docker push <registry-name>.azurecr.io/missing-trees-api:latest
```

## Algorithm

The missing tree detection algorithm works as follows:

1. **Grid Parameter Detection**: If not provided, the algorithm analyzes existing tree positions to determine:
   - Number of rows and columns
   - Spacing between rows and columns
   
2. **Expected Grid Generation**: Creates a complete grid based on detected or provided parameters

3. **Gap Detection**: Compares expected positions with actual positions to identify missing trees

4. **Tolerance Handling**: Uses a configurable tolerance (default 1.0m) to account for minor positioning variations

## Project Structure

```
.
├── main.py                 # FastAPI application
├── missing_trees.py        # Core detection algorithm
├── test_main.py           # API integration tests
├── test_missing_trees.py  # Unit tests for detection algorithm
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .dockerignore         # Docker ignore rules
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## License

MIT