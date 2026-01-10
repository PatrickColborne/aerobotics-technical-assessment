import numpy as np
from scipy.spatial import cKDTree

class DualAxisScanner:
    def __init__(self, data):
        self.raw_data = np.array(data)
        self.ref_lat = np.median(self.raw_data[:, 0])
        self.ref_lon = np.median(self.raw_data[:, 1])
        self.R = 6371000
        self.meters = self._to_meters(self.raw_data)

    def _to_meters(self, coords):
        lats = np.radians(coords[:, 0])
        lons = np.radians(coords[:, 1])
        ref_lat_rad = np.radians(self.ref_lat)
        ref_lon_rad = np.radians(self.ref_lon)
        x = (lons - ref_lon_rad) * np.cos(ref_lat_rad) * self.R
        y = (lats - ref_lat_rad) * self.R
        return np.column_stack((x, y))

    def _to_latlon(self, meters):
        x = meters[:, 0]
        y = meters[:, 1]
        ref_lat_rad = np.radians(self.ref_lat)
        lat_rad = (y / self.R) + ref_lat_rad
        lon_rad = (x / (self.R * np.cos(ref_lat_rad))) + np.radians(self.ref_lon)
        return np.column_stack((np.degrees(lat_rad), np.degrees(lon_rad)))

    def get_dual_angles(self):
        """
        Returns two dominant angles:
        1. Primary Angle (Row Direction)
        2. Secondary Angle (Column Direction, NOT necessarily 90 deg from rows)
        """
        tree = cKDTree(self.meters)
        dists, indices = tree.query(self.meters, k=2)
        neighbors = self.meters[indices[:, 1]]
        diffs = neighbors - self.meters
        angles = np.arctan2(diffs[:, 1], diffs[:, 0])
        deg_angles = np.degrees(angles) % 180

        # High res histogram
        bins = np.linspace(0, 180, 361)  # 0.5 deg bins
        hist, bin_edges = np.histogram(deg_angles, bins=bins)

        # 1. Find Primary Angle
        peak_idx = np.argmax(hist)
        angle1 = bin_edges[peak_idx]

        # 2. Find Secondary Angle
        # Mask out the primary angle and its neighbors (+/- 15 degrees)
        # to find the next dominant direction (columns)
        mask_radius = 15
        # Handle wrapping around 0/180
        indices_to_mask = []
        for i in range(len(bin_edges) - 1):
            diff = abs(bin_edges[i] - angle1)
            if diff > 90: diff = 180 - diff
            if diff < mask_radius:
                indices_to_mask.append(i)

        hist[indices_to_mask] = 0

        peak2_idx = np.argmax(hist)
        angle2 = bin_edges[peak2_idx]

        return np.radians(angle1), np.radians(angle2)

    def scan_axis(self, angle, debug_color=None):
        """Generic function to rotate by 'angle', cluster rows in Y, and find gaps in X."""

        # Rotate the orchard so that rows align with X-axis and columns with Y-axis
        c, s = np.cos(-angle), np.sin(-angle)
        R = np.array([[c, -s], [s, c]])
        rotated = np.dot(self.meters, R.T)

        # Dynamic Row Threshold
        tree = cKDTree(rotated)
        dists, _ = tree.query(rotated, k=2)
        nearest_dist_median = np.median(dists[:, 1])
        row_sep_threshold = nearest_dist_median * 0.2  # 10% of tree spacing

        # Cluster Rows (Y-axis)
        sorted_idx = np.argsort(rotated[:, 1])
        sorted_y = rotated[sorted_idx, 1]
        y_diffs = np.diff(sorted_y)
        row_breaks = np.where(y_diffs > row_sep_threshold)[0] + 1
        row_indices = np.split(sorted_idx, row_breaks)

        found_gaps = []

        for tree_indices in row_indices:
            if len(tree_indices) < 2: continue
            row_trees = rotated[tree_indices]

            # Sort by X (Walking along the row/column)
            x_sorted_idx = np.argsort(row_trees[:, 0])
            xs = row_trees[x_sorted_idx, 0]
            ys = row_trees[x_sorted_idx, 1]

            x_diffs = np.diff(xs)
            if len(x_diffs) == 0: continue

            median_spacing = np.median(x_diffs)

            # Gap detection (Tolerance 1.8x)
            gap_indices = np.where(x_diffs > median_spacing * 1.8)[0]

            for i in gap_indices:
                gap_size = x_diffs[i]
                start_x, start_y = xs[i], ys[i]
                end_x, end_y = xs[i + 1], ys[i + 1]

                num_segments = int(round(gap_size / median_spacing))
                missing_count = num_segments - 1

                for m in range(1, missing_count + 1):
                    fraction = m / num_segments
                    ix = start_x + (end_x - start_x) * fraction
                    iy = start_y + (end_y - start_y) * fraction
                    found_gaps.append([ix, iy])

        # Rotate gaps back to Global Meters
        if not found_gaps: return []
        inv_R = np.linalg.inv(R)
        return np.dot(np.array(found_gaps), inv_R.T).tolist()

    def merge_close_points(self, points, tolerance):
        """
        Removes duplicates by merging points that are within 'tolerance' meters.
        """
        if len(points) == 0:
            return np.array([])

        points = np.array(points)
        tree = cKDTree(points)

        processed_indices = set()
        unique_points = []

        for i in range(len(points)):
            if i in processed_indices:
                continue

            # Keep this point
            unique_points.append(points[i])

            # Find neighbors within dynamic tolerance
            neighbors = tree.query_ball_point(points[i], r=tolerance)
            processed_indices.update(neighbors)

        return np.array(unique_points)

    def solve(self):
        # 1. Detect Angles
        ang1, ang2 = self.get_dual_angles()
        print(f"Dual-Axis Detection :: Angle 1: {np.degrees(ang1):.1f} deg | Angle 2: {np.degrees(ang2):.1f} deg")

        # 2. Scan Both Directions
        gaps1 = self.scan_axis(ang1)
        gaps2 = self.scan_axis(ang2)

        # 3. Combine Results
        all_gaps = gaps1 + gaps2
        if not all_gaps:
            return np.array([]), np.array([])

        # --- DYNAMIC TOLERANCE CALCULATION ---
        # Get the median spacing of the ACTUAL trees to set the scale
        tree_kd = cKDTree(self.meters)
        dists, _ = tree_kd.query(self.meters, k=2)
        median_tree_spacing = np.median(dists[:, 1])

        # Set tolerance to 40% of the tree spacing
        # This is large enough to catch floating point drift,
        # but small enough ( < 50%) to never merge two valid adjacent spots.
        merge_tolerance = median_tree_spacing * 0.4

        print(f"Auto-calculated Merge Tolerance: {merge_tolerance:.3f}m (based on spacing {median_tree_spacing:.2f}m)")
        # -------------------------------------

        # 4. Deduplicate
        unique_gaps = self.merge_close_points(all_gaps, tolerance=merge_tolerance)

        print(f"Merged {len(all_gaps)} detections -> {len(unique_gaps)} unique missing trees.")

        return self._to_latlon(unique_gaps), unique_gaps
