"""
Unit tests for the missing trees detection service.
"""
import pytest
from missing_trees import MissingTreesDetector


class TestMissingTreesDetector:
    """Test cases for MissingTreesDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = MissingTreesDetector(tolerance=1.0)
    
    def test_no_missing_trees_perfect_grid(self):
        """Test with a perfect 3x3 grid - no missing trees."""
        positions = [
            (0, 0), (5, 0), (10, 0),
            (0, 5), (5, 5), (10, 5),
            (0, 10), (5, 10), (10, 10)
        ]
        
        missing = self.detector.detect_missing_trees(positions)
        assert len(missing) == 0
    
    def test_one_missing_tree(self):
        """Test with one missing tree in a 3x3 grid."""
        positions = [
            (0, 0), (5, 0), (10, 0),
            (0, 5), (10, 5),  # Missing (5, 5)
            (0, 10), (5, 10), (10, 10)
        ]
        
        missing = self.detector.detect_missing_trees(positions)
        assert len(missing) == 1
        assert (5.0, 5.0) in missing
    
    def test_multiple_missing_trees(self):
        """Test with multiple missing trees."""
        positions = [
            (0, 0), (10, 0),  # Missing (5, 0)
            (0, 5), (5, 5), (10, 5),
            (5, 10), (10, 10)  # Missing (0, 10)
        ]
        
        missing = self.detector.detect_missing_trees(positions)
        assert len(missing) == 2
        assert (5.0, 0.0) in missing
        assert (0.0, 10.0) in missing
    
    def test_empty_orchard(self):
        """Test with empty tree positions."""
        positions = []
        missing = self.detector.detect_missing_trees(positions)
        assert len(missing) == 0
    
    def test_single_tree(self):
        """Test with only one tree."""
        positions = [(0, 0)]
        missing = self.detector.detect_missing_trees(positions)
        # Should detect grid parameters but no missing trees with single point
        assert len(missing) == 0
    
    def test_custom_spacing(self):
        """Test with custom row and column spacing."""
        positions = [
            (0, 0), (3, 0),  # Missing (6, 0)
            (0, 4), (3, 4), (6, 4),
            (0, 8), (3, 8), (6, 8)
        ]
        
        missing = self.detector.detect_missing_trees(
            positions,
            expected_rows=3,
            expected_cols=3,
            row_spacing=4.0,
            col_spacing=3.0
        )
        
        assert len(missing) == 1
        assert (6.0, 0.0) in missing
    
    def test_explicit_grid_parameters(self):
        """Test with explicitly provided grid parameters."""
        positions = [
            (0, 0), (5, 0),
            (0, 5), (5, 5)
        ]
        
        # Expect a 3x3 grid but only 2x2 trees exist
        missing = self.detector.detect_missing_trees(
            positions,
            expected_rows=3,
            expected_cols=3,
            row_spacing=5.0,
            col_spacing=5.0
        )
        
        # Should find 5 missing trees: (10,0), (0,10), (5,10), (10,5), (10,10)
        assert len(missing) == 5
        assert (10.0, 0.0) in missing
        assert (0.0, 10.0) in missing
        assert (5.0, 10.0) in missing
        assert (10.0, 5.0) in missing
        assert (10.0, 10.0) in missing
    
    def test_tolerance_handling(self):
        """Test that tolerance correctly identifies nearby trees."""
        detector = MissingTreesDetector(tolerance=1.0)
        
        # Trees with slight variations should still be detected as present
        positions = [
            (0, 0), (5.1, 0), (10, 0),
            (0, 5), (4.9, 5.1), (10, 5),
            (0, 10), (5, 10), (10.2, 10)
        ]
        
        # With explicit parameters to avoid auto-detection issues
        missing = detector.detect_missing_trees(
            positions,
            expected_rows=3,
            expected_cols=3,
            row_spacing=5.0,
            col_spacing=5.0
        )
        # Should find no missing trees due to tolerance handling minor variations
        assert len(missing) == 0
    
    def test_irregular_spacing(self):
        """Test with irregular spacing in the grid."""
        positions = [
            (0, 0), (5, 0), (10, 0),
            (0, 6), (5, 6), (10, 6),
            (0, 12), (10, 12)  # Missing (5, 12)
        ]
        
        missing = self.detector.detect_missing_trees(positions)
        # Should detect the missing tree
        assert len(missing) >= 1
        assert (5.0, 12.0) in missing
