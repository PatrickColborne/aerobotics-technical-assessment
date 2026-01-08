"""
Service for detecting missing trees in an orchard.

This module provides functionality to identify missing trees based on expected
orchard layout patterns.
"""
from typing import List, Tuple, Set
import math


class MissingTreesDetector:
    """Detector for finding missing trees in an orchard based on grid patterns."""
    
    def __init__(self, tolerance: float = 1.0):
        """
        Initialize the missing trees detector.
        
        Args:
            tolerance: Distance tolerance for considering positions as matching (in meters)
        """
        self.tolerance = tolerance
    
    def detect_missing_trees(
        self, 
        tree_positions: List[Tuple[float, float]],
        expected_rows: int = None,
        expected_cols: int = None,
        row_spacing: float = None,
        col_spacing: float = None
    ) -> List[Tuple[float, float]]:
        """
        Detect missing trees in an orchard based on expected grid pattern.
        
        Args:
            tree_positions: List of (x, y) coordinates of existing trees
            expected_rows: Expected number of rows (auto-detected if None)
            expected_cols: Expected number of columns (auto-detected if None)
            row_spacing: Expected spacing between rows (auto-detected if None)
            col_spacing: Expected spacing between columns (auto-detected if None)
            
        Returns:
            List of (x, y) coordinates where trees are expected but missing
        """
        if not tree_positions:
            return []
        
        # Auto-detect grid parameters if not provided
        if any(param is None for param in [expected_rows, expected_cols, row_spacing, col_spacing]):
            detected_params = self._detect_grid_parameters(tree_positions)
            expected_rows = expected_rows or detected_params['rows']
            expected_cols = expected_cols or detected_params['cols']
            row_spacing = row_spacing or detected_params['row_spacing']
            col_spacing = col_spacing or detected_params['col_spacing']
        
        # Generate expected grid positions
        expected_positions = self._generate_grid(
            tree_positions, expected_rows, expected_cols, row_spacing, col_spacing
        )
        
        # Find missing positions
        missing_positions = self._find_missing_positions(tree_positions, expected_positions)
        
        return missing_positions
    
    def _detect_grid_parameters(self, positions: List[Tuple[float, float]]) -> dict:
        """
        Auto-detect grid parameters from existing tree positions.
        
        Args:
            positions: List of (x, y) coordinates of existing trees
            
        Returns:
            Dictionary with detected rows, cols, row_spacing, and col_spacing
        """
        if len(positions) < 2:
            return {'rows': 1, 'cols': len(positions), 'row_spacing': 0, 'col_spacing': 0}
        
        # Extract x and y coordinates
        xs = sorted(set(round(x, 1) for x, y in positions))
        ys = sorted(set(round(y, 1) for x, y in positions))
        
        # Estimate spacing by finding most common distances
        x_diffs = []
        y_diffs = []
        
        for i in range(len(xs) - 1):
            x_diffs.append(xs[i + 1] - xs[i])
        
        for i in range(len(ys) - 1):
            y_diffs.append(ys[i + 1] - ys[i])
        
        # Use median spacing to handle irregularities
        col_spacing = sorted(x_diffs)[len(x_diffs) // 2] if x_diffs else 5.0
        row_spacing = sorted(y_diffs)[len(y_diffs) // 2] if y_diffs else 5.0
        
        # Estimate number of rows and columns
        cols = len(xs)
        rows = len(ys)
        
        return {
            'rows': rows,
            'cols': cols,
            'row_spacing': row_spacing,
            'col_spacing': col_spacing
        }
    
    def _generate_grid(
        self,
        reference_positions: List[Tuple[float, float]],
        rows: int,
        cols: int,
        row_spacing: float,
        col_spacing: float
    ) -> Set[Tuple[float, float]]:
        """
        Generate expected grid positions based on parameters.
        
        Args:
            reference_positions: Existing tree positions to use as reference
            rows: Number of rows
            cols: Number of columns
            row_spacing: Spacing between rows
            col_spacing: Spacing between columns
            
        Returns:
            Set of expected (x, y) positions rounded to 1 decimal place
        """
        # Find the origin point (bottom-left corner)
        min_x = min(x for x, y in reference_positions)
        min_y = min(y for x, y in reference_positions)
        
        expected = set()
        for row in range(rows):
            for col in range(cols):
                x = round(min_x + col * col_spacing, 1)
                y = round(min_y + row * row_spacing, 1)
                expected.add((x, y))
        
        return expected
    
    def _find_missing_positions(
        self,
        actual_positions: List[Tuple[float, float]],
        expected_positions: Set[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Find positions that are expected but not present in actual positions.
        
        Args:
            actual_positions: List of actual tree positions
            expected_positions: Set of expected tree positions
            
        Returns:
            List of missing positions
        """
        # Round actual positions for comparison
        actual_set = set((round(x, 1), round(y, 1)) for x, y in actual_positions)
        
        # Find positions in expected but not in actual
        missing = []
        for expected_pos in expected_positions:
            # Check if any actual position is within tolerance
            found = False
            for actual_pos in actual_set:
                distance = math.sqrt(
                    (expected_pos[0] - actual_pos[0]) ** 2 +
                    (expected_pos[1] - actual_pos[1]) ** 2
                )
                if distance <= self.tolerance:
                    found = True
                    break
            
            if not found:
                missing.append(expected_pos)
        
        return sorted(missing)
