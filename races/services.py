from collections import defaultdict
from math import ceil
from races.models import RaceEvent, RaceEntry


def calculate_points(position, max_points=14):
    """
    Convert finishing position into points.
    """
    if not position:
        return 0

    points = max_points - (position - 1)
    return max(points, 0)

#----------------------------------------------------------#

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

#----------------------------------------------------------#

# Corrected = (Elapsed × 1000 / PY) × (max_laps / boat_laps)
def corrected_time(elapsed_seconds, py, laps, max_laps):
    if not elapsed_seconds or not py or not laps:
        return None

    base = (elapsed_seconds * 1000) / py
    lap_factor = max_laps / laps

    return base * lap_factor

#----------------------------------------------------------#

def format_seconds(total):
    if total is None:
        return ""

    total = int(total)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60

    # if h:
    #     return f"{h}:{m:02}:{s:02}"
    return f"{h:02}:{m}:{s:02}"

#----------------------------------------------------------#

def build_race_state(race_id):
    events = RaceEvent.objects.filter(race_id=race_id).order_by(
        "device_id", "sequence"
    )

    state = {
        "started": False,
        "finished": False,
        "race_time": 0,
        "boats": {}
    }

####
    events = list(
        RaceEvent.objects
        .filter(race_id=race_id)
        .order_by("device_id", "sequence")
    )

    # find index of last restart
    last_restart_index = -1
    for i, ev in enumerate(events):
        if ev.event_type == "restart":
            last_restart_index = i

    # cut history
    if last_restart_index >= 0:
        events = events[last_restart_index + 1:]


####

    # initialise boats from DB
    entries = RaceEntry.objects.filter(race_id=race_id).select_related(
        "helm", "boat"
    )

    for e in entries:
        state["boats"][e.id] = {
            "entry_id": e.id,
            "helm": e.helm.get_short_name(),
            "sail": e.boat.sail_number,
            "py": float(e.py_used or 0),
            "laps": 0,
            "times": [],
            "last": 0,
            "corrected": 0,
            "boat_class": e.boat_type_name
        }

    # replay events
    for ev in events:

        if ev.event_type == "start":
            state["started"] = True

        elif ev.event_type == "lap" and ev.race_entry_id:
            b = state["boats"][ev.race_entry_id]
            b["laps"] += 1
            b["times"].append(ev.race_seconds)
            b["last"] = ev.race_seconds
            state["race_time"] = max(state["race_time"], ev.race_seconds or 0)

        elif ev.event_type == "undo" and ev.race_entry_id:
            b = state["boats"][ev.race_entry_id]
            if b["laps"] > 0:
                b["laps"] -= 1
                b["times"].pop()
                b["last"] = b["times"][-1] if b["times"] else 0

        elif ev.event_type == "finish":
            state["finished"] = True

    # -------------------------------------------------
    # CALCULATE CORRECTED
    # -------------------------------------------------
    max_laps = max((b["laps"] for b in state["boats"].values()), default=0)

    for b in state["boats"].values():
        if b["laps"] > 0 and b["py"]:
            projected = b["last"] * (max_laps / b["laps"])
            b["corrected"] = projected * 1000 / b["py"]

    # -------------------------------------------------
    # POSITIONS
    # -------------------------------------------------
    actual = sorted(
        state["boats"].values(),
        key=lambda x: (-x["laps"], x["last"])
    )

    for i, b in enumerate(actual, 1):
        b["actual_pos"] = i

    corrected = sorted(
        state["boats"].values(),
        key=lambda x: x["corrected"] or 999999
    )

    for i, b in enumerate(corrected, 1):
        b["corrected_pos"] = i

    return state


