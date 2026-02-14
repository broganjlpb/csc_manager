def calculate_points(position, max_points=14):
    """
    Convert finishing position into points.
    """
    if not position:
        return 0

    points = max_points - (position - 1)
    return max(points, 0)
