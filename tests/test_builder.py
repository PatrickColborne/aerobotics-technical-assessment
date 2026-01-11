import math
import random

def rotate_point(origin, angle_deg, distance):
    angle_rad = math.radians(angle_deg)
    dx = distance * math.cos(angle_rad)
    dy = distance * math.sin(angle_rad)
    return [origin[0] + dx, origin[1] + dy]

rows, cols = 10, 10
lat_start, lon_start = -32.328, 18.826
lat_step, lon_step = 0.0002, 0.0002  # step size in degrees
origin = [lat_start, lon_start]

axis1_angle = 0
axis2_angle = 90

full_grid = []
for i in range(rows):
    for j in range(cols):
        # Move i steps along axis1, j steps along axis2
        pt1 = rotate_point(origin, axis1_angle, i * lat_step)
        pt2 = rotate_point(origin, axis2_angle, j * lon_step)
        # Combine the two displacements
        lat = pt1[0] + (pt2[0] - origin[0])
        lon = pt1[1] + (pt2[1] - origin[1])
        full_grid.append([lat, lon])

# Remove 5 points for missing trees (spread out)
missing_indices = random.sample(range(len(full_grid)), 5)
grid_data = [pt for idx, pt in enumerate(full_grid) if idx not in missing_indices]

print(grid_data)