"""
FastAPI application for detecting missing trees in orchards.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from missing_trees import MissingTreesDetector

app = FastAPI(
    title="Missing Trees Detection API",
    description="API for detecting missing trees in orchard layouts",
    version="1.0.0"
)

detector = MissingTreesDetector(tolerance=1.0)


class TreePosition(BaseModel):
    """Represents a tree position coordinate."""
    x: float = Field(..., description="X coordinate of the tree")
    y: float = Field(..., description="Y coordinate of the tree")


class OrchardRequest(BaseModel):
    """Request model for missing trees detection."""
    tree_positions: List[TreePosition] = Field(
        ..., 
        description="List of existing tree positions in the orchard"
    )
    expected_rows: Optional[int] = Field(
        None, 
        description="Expected number of rows (auto-detected if not provided)"
    )
    expected_cols: Optional[int] = Field(
        None, 
        description="Expected number of columns (auto-detected if not provided)"
    )
    row_spacing: Optional[float] = Field(
        None, 
        description="Expected spacing between rows in meters (auto-detected if not provided)"
    )
    col_spacing: Optional[float] = Field(
        None, 
        description="Expected spacing between columns in meters (auto-detected if not provided)"
    )


class OrchardResponse(BaseModel):
    """Response model for missing trees detection."""
    missing_trees: List[TreePosition] = Field(
        ..., 
        description="List of positions where trees are expected but missing"
    )
    total_missing: int = Field(
        ..., 
        description="Total count of missing trees"
    )


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Missing Trees Detection API",
        "version": "1.0.0",
        "description": "API for detecting missing trees in orchard layouts"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/detect-missing-trees", response_model=OrchardResponse)
async def detect_missing_trees(request: OrchardRequest):
    """
    Detect missing trees in an orchard based on expected grid pattern.
    
    Args:
        request: OrchardRequest containing tree positions and optional grid parameters
        
    Returns:
        OrchardResponse with list of missing tree positions and count
        
    Raises:
        HTTPException: If input validation fails or processing error occurs
    """
    try:
        if not request.tree_positions:
            raise HTTPException(status_code=400, detail="Tree positions cannot be empty")
        
        # Convert TreePosition objects to tuples
        tree_positions = [(pos.x, pos.y) for pos in request.tree_positions]
        
        # Detect missing trees
        missing_positions = detector.detect_missing_trees(
            tree_positions=tree_positions,
            expected_rows=request.expected_rows,
            expected_cols=request.expected_cols,
            row_spacing=request.row_spacing,
            col_spacing=request.col_spacing
        )
        
        # Convert back to TreePosition objects
        missing_trees = [TreePosition(x=x, y=y) for x, y in missing_positions]
        
        return OrchardResponse(
            missing_trees=missing_trees,
            total_missing=len(missing_trees)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
