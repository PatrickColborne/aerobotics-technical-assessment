import numpy as np
from scipy.spatial import cKDTree
from typing import List, Tuple, Optional


class OrchardScanner:
    def __init__(self, data: List[List[float]]):
        """
        Initialize with a list of [lat, lon] coordinates.
        Automatic projection to local metric space.
        """
        self.raw_data = np.array(data)
        self.R = 6371000  # Earth radius in meters

        # Reference point for local projection (Median avoids outliers)
        self.ref_lat = np.median(self.raw_data[:, 0])
        self.ref_lon = np.median(self.raw_data[:, 1])

        # Pre-compute radians for the reference point
        self.ref_lat_rad = np.radians(self.ref_lat)
        self.ref_lon_rad = np.radians(self.ref_lon)

        # Project immediately to meters
        self.meters = self._to_meters(self.raw_data)

    # --- 1. PROJECTION HELPERS ---
    def _to_meters(self, coords: np.ndarray) -> np.ndarray:
        """Projects Lat/Lon to Local X/Y Meters (Flat Earth Approximation)."""
        lats = np.radians(coords[:, 0])
        lons = np.radians(coords[:, 1])
        x = (lons - self.ref_lon_rad) * np.cos(self.ref_lat_rad) * self.R
        y = (lats - self.ref_lat_rad) * self.R
        return np.column_stack((x, y))

    def _to_latlon(self, meters: np.ndarray) -> np.ndarray:
        """Projects Local X/Y Meters back to Lat/Lon."""
        if len(meters) == 0:
            return np.array([])
        x = meters[:, 0]
        y = meters[:, 1]
        lat_rad = (y / self.R) + self.ref_lat_rad
        lon_rad = (x / (self.R * np.cos(self.ref_lat_rad))) + self.ref_lon_rad
        return np.column_stack((np.degrees(lat_rad), np.degrees(lon_rad)))

    # --- 2. ORIENTATION LOGIC ---
    def get_grid_orientation(self) -> Tuple[float, float]:
        """
        Determines the two dominant axes (Row vs Column angle) using a histogram
        of nearest-neighbor vectors.
        """
        # We don't need the whole dataset to find angles, a sample is faster for massive datasets.
        # But cKDTree is fast enough for <100k points.
        tree = cKDTree(self.meters)
        dists, indices = tree.query(self.meters, k=2)

        # Calculate vector to nearest neighbor
        neighbors = self.meters[indices[:, 1]]
        diffs = neighbors - self.meters
        angles = np.arctan2(diffs[:, 1], diffs[:, 0])
        deg_angles = np.degrees(angles) % 180

        # High res histogram (0.5 deg bins)
        bins = np.linspace(0, 180, 361)
        hist, bin_edges = np.histogram(deg_angles, bins=bins)

        # Find Primary Angle (Angle with most alignment)
        peak_idx = np.argmax(hist)
        angle1 = bin_edges[peak_idx]

        # Find Secondary Angle
        # Mask out the primary angle (+/- 15 deg) to find the orthogonal-ish direction
        centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        diff = np.abs(centers - angle1)
        # Handle 0/180 wrap-around distance
        diff = np.minimum(diff, 180 - diff)

        mask_indices = np.where(diff < 15)[0]
        hist[mask_indices] = 0

        peak2_idx = np.argmax(hist)
        angle2 = bin_edges[peak2_idx]

        return np.radians(angle1), np.radians(angle2)

    # --- 3. CORE SCANNING LOGIC ---
    def _rotate_points(self, points: np.ndarray, angle: float) -> Tuple[np.ndarray, np.ndarray]:
        """Rotates points by angle and returns the rotation matrix used."""
        c, s = np.cos(-angle), np.sin(-angle)
        R = np.array([[c, -s], [s, c]])
        return np.dot(points, R.T), R

    def scan_axis(self, angle: float) -> np.ndarray:
        """
        Rotates the orchard, identifies rows, and finds missing trees within those rows.
        Vectorized for performance.
        """
        # 1. Rotate orchard to align rows with X-axis
        rotated, R_matrix = self._rotate_points(self.meters, angle)

        # 2. Dynamic Thresholds
        tree = cKDTree(rotated)
        dists, _ = tree.query(rotated, k=2)
        median_spacing = np.median(dists[:, 1])
        row_sep_threshold = median_spacing * 0.2

        # 3. Identify Rows (Cluster by Y-coordinate)
        # Sort by Y to find row breaks
        sort_idx = np.argsort(rotated[:, 1])
        rotated_sorted = rotated[sort_idx]

        # Where does Y jump significantly? That's a new row.
        y_diffs = np.diff(rotated_sorted[:, 1])
        row_breaks = np.where(y_diffs > row_sep_threshold)[0] + 1
        row_groups = np.split(rotated_sorted, row_breaks)

        all_new_points = []

        # 4. Process Rows (Iterate rows, but vectorize inside the row)
        for row_points in row_groups:
            if len(row_points) < 2:
                continue

            # Sort by X (Walking along the row)
            row_points = row_points[np.argsort(row_points[:, 0])]

            xs = row_points[:, 0]
            x_diffs = np.diff(xs)

            # Local spacing for this row (robust to slight variations)
            local_spacing = np.median(x_diffs)

            # Find indices where the gap is large enough to be a missing tree
            # Tolerance: 1.8x spacing means "definitely skipped at least one"
            gap_indices = np.where(x_diffs > local_spacing * 1.8)[0]

            if len(gap_indices) == 0:
                continue

            # 5. Vectorized Gap Filling
            for idx in gap_indices:
                gap_size = x_diffs[idx]
                start_pt = row_points[idx]
                end_pt = row_points[idx + 1]

                # How many trees are missing?
                num_segments = int(round(gap_size / local_spacing))
                missing_count = num_segments - 1

                if missing_count > 0:
                    # Generate ratios: [0.33, 0.66] for 2 missing trees
                    ratios = np.linspace(0, 1, num_segments + 1)[1:-1]

                    # Interpolate X and Y coordinates simultaneously
                    # shape: (N_missing, 2)
                    new_pts = start_pt + np.outer(ratios, (end_pt - start_pt))
                    all_new_points.append(new_pts)

        if not all_new_points:
            return np.array([])

        # Concatenate all findings and rotate back to global frame
        found_gaps_rotated = np.vstack(all_new_points)

        # Inverse rotation: v_global = v_rotated * R
        # (Since R was constructed as global->rotated)
        inv_R = np.linalg.inv(R_matrix)
        return np.dot(found_gaps_rotated, inv_R.T)

    # --- 4. POST-PROCESSING ---
    def deduplicate(self, points: np.ndarray, tolerance: float) -> np.ndarray:
        """
        Removes duplicates using Vectorized Nearest Neighbor search.
        Logic: If Point A and Point B are close, keep the one with the lower index.
        """
        if len(points) == 0:
            return np.array([])

        # Build tree of the found gaps
        tree = cKDTree(points)

        # Find neighbors for every point within tolerance
        # result is a sparse list of neighbors
        dists, indices = tree.query(points, k=2, distance_upper_bound=tolerance)

        # 'indices' will contain [self_index, neighbor_index]
        # If neighbor_index is N (infinity placeholder), it means no neighbor found.

        # We flag a point for removal if it has a neighbor within tolerance
        # AND that neighbor has a smaller index (simple tie-breaker)
        has_neighbor = dists[:, 1] != float('inf')
        neighbor_idx = indices[:, 1]

        # Vectorized check: am I the duplicate? (Is my neighbor's index < my index?)
        # We only keep the "first" occurrence of any cluster.
        is_duplicate = has_neighbor & (neighbor_idx < np.arange(len(points)))

        return points[~is_duplicate]

    # --- 5. MAIN EXECUTION ---
    def solve(self):
        # 1. Detect Orientation
        ang1, ang2 = self.get_grid_orientation()
        print(f"Angle 1: {np.degrees(ang1):.1f} deg | Angle 2: {np.degrees(ang2):.1f} deg")

        # 2. Scan both axes
        gaps1 = self.scan_axis(ang1)
        gaps2 = self.scan_axis(ang2)

        # 3. Combine
        if len(gaps1) == 0 and len(gaps2) == 0:
            return np.array([]), np.array([])

        if len(gaps1) == 0:
            all_gaps = gaps2
        elif len(gaps2) == 0:
            all_gaps = gaps1
        else:
            all_gaps = np.vstack((gaps1, gaps2))

        # 4. Calculate Tolerance based on real tree spacing
        tree_kd = cKDTree(self.meters)
        dists, _ = tree_kd.query(self.meters, k=2)
        median_tree_spacing = np.median(dists[:, 1])
        merge_tolerance = median_tree_spacing * 0.4
        print(f"Merge Tolerance: {merge_tolerance:.3f}m")

        # 5. Deduplicate
        unique_gaps = self.deduplicate(all_gaps, tolerance=merge_tolerance)
        print(f"Found {len(unique_gaps)} unique missing trees.")

        return self._to_latlon(unique_gaps), unique_gaps