from collections import defaultdict
from math import ceil


def calculate_points(position, max_points=14):
    """
    Convert finishing position into points.
    """
    if not position:
        return 0

    points = max_points - (position - 1)
    return max(points, 0)

def calculate_league_table(league):
    """
    Returns sorted standings for a league.
    """

    entries = (
        league.races
        .filter(status="finished")
        .prefetch_related("entries__helm", "entries__crew")
    )

    sailor_points = defaultdict(list)

    # Collect points
    for race in entries:
        for e in race.entries.all():
            if hasattr(e, "points"):
                pts = e.points
            else:
                # fallback
                if not e.finish_position:
                    pts = 0
                else:
                    pts = max(14 - (e.finish_position - 1), 0)

            sailor_points[e.helm].append(pts)

            if e.crew:
                sailor_points[e.crew].append(pts)

    if not sailor_points:
        return []

    max_races = max(len(v) for v in sailor_points.values())
    discard_limit = ceil(max_races * 0.66)

    standings = []

    for sailor, scores in sailor_points.items():
        best = sorted(scores, reverse=True)[:discard_limit]

        standings.append({
            "sailor": sailor,
            "sailed": len(scores),
            "counted": len(best),
            "total": sum(best),
            "scores": scores,
        })

    standings.sort(key=lambda x: x["total"], reverse=True)

    return standings