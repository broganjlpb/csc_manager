from collections import defaultdict
from math import ceil
from races.models import RaceEvent, RaceEntry, ResultSet, ResultSetEntry, RaceEntry
from django.utils import timezone


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

def build_race_state(race_id, attempt=None):

    all_events = list(
        RaceEvent.objects.filter(race_id=race_id)
        .order_by("device_id", "sequence")
    )

    # -------------------------------------------------
    # FIND RESTART POINTS
    # -------------------------------------------------
    restart_indexes = [-1]

    for i, ev in enumerate(all_events):
        if ev.event_type == "restart":
            restart_indexes.append(i)

    total_attempts = len(restart_indexes)

    if attempt is None or attempt > total_attempts:
        attempt = total_attempts

    start_index = restart_indexes[attempt - 1] + 1
    end_index = (
        restart_indexes[attempt]
        if attempt < total_attempts
        else len(all_events)
    )

    events = all_events[start_index:end_index]

    # -------------------------------------------------
    # INITIAL STATE
    # -------------------------------------------------
    state = {
        "started": False,
        "finished": False,
        "race_time": 0,
        "attempt": attempt,
        "total_attempts": total_attempts,
        "boats": {},
        "history": [],   # ⭐ important
    }

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
            "corrected": None,
            "boat_class": getattr(e.boat, "boat_type", None).name
                if getattr(e.boat, "boat_type", None) else "",
        }

    # -------------------------------------------------
    # SNAPSHOT FUNCTION
    # -------------------------------------------------
    def snapshot(time_value):

        boats = list(state["boats"].values())

        # corrected at this moment
        max_laps = max((b["laps"] for b in boats), default=0)

        for b in boats:
            if b["laps"] > 0 and b["py"]:
                projected = b["last"] * (max_laps / b["laps"])
                b["corrected"] = projected * 1000 / b["py"]
            else:
                b["corrected"] = None

        # actual
        actual = sorted(
            boats,
            key=lambda x: (-x["laps"], x["last"] or 999999)
        )
        for i, b in enumerate(actual, 1):
            b["actual_pos"] = i

        # corrected
        corrected = sorted(
            boats,
            key=lambda x: x["corrected"] if x["corrected"] is not None else 999999
        )
        for i, b in enumerate(corrected, 1):
            b["corrected_pos"] = i

        # ⭐ append (do NOT reset!)
        state["history"].append({
            "time": time_value,
            "boats": {
                b["entry_id"]: {
                    "actual_pos": b["actual_pos"],
                    "corrected_pos": b["corrected_pos"],
                }
                for b in boats
            }
        })

    # -------------------------------------------------
    # REPLAY EVENTS
    # -------------------------------------------------
    for ev in events:

        if ev.event_type == "start":
            state["started"] = True

        elif ev.event_type == "lap" and ev.race_entry_id:
            b = state["boats"][ev.race_entry_id]

            b["laps"] += 1
            b["times"].append(ev.race_seconds)
            b["last"] = ev.race_seconds

            state["race_time"] = max(state["race_time"], ev.race_seconds or 0)

            snapshot(state["race_time"])  # ⭐ magic moment

        elif ev.event_type == "undo" and ev.race_entry_id:
            b = state["boats"][ev.race_entry_id]
            if b["laps"] > 0:
                b["laps"] -= 1
                b["times"].pop()
                b["last"] = b["times"][-1] if b["times"] else 0

        elif ev.event_type == "finish":
            state["finished"] = True

    # -------------------------------------------------
    # FINAL POSITIONS (for table)
    # -------------------------------------------------
    if state["history"]:
        final = state["history"][-1]["boats"]
        for boat_id, b in state["boats"].items():
            if boat_id in final:
                b["actual_pos"] = final[boat_id]["actual_pos"]
                b["corrected_pos"] = final[boat_id]["corrected_pos"]

    return state

#----------------------------------------------------------#

def derive_race_state(race):

    if race.is_cancelled:
        return "CANCELLED"

    has_published = race.result_sets.filter(
        state=ResultSet.State.PUBLISHED
    ).exists()

    if has_published:
        return "PUBLISHED"

    has_finished_event = RaceEvent.objects.filter(
        race=race,
        event_type="finish"
    ).exists()

    if has_finished_event:
        return "UNCONFIRMED"

    has_started = RaceEvent.objects.filter(
        race=race,
        event_type="start"
    ).exists()

    if has_started:
        return "LIVE"

    if race.raceentry_set.exists():
        return "READY"

    return "DRAFT"

#----------------------------------------------------------#

def get_or_create_user_resultset(race, user, source):
    result_set, created = ResultSet.objects.get_or_create(
        race=race,
        created_by=user,
        source=source,
        defaults={"state": ResultSet.State.DRAFT},
    )

    if not created:
        return result_set

    # -------------------------------------------------
    # Populate if needed
    # -------------------------------------------------

    if source == ResultSet.Source.MANUAL_TIME:
        populate_manual_time(result_set)

    elif source == ResultSet.Source.MANUAL_POSITION:
        populate_manual_position(result_set)

    return result_set

#----------------------------------------------------------#

def populate_manual_time(result_set):
    race = result_set.race
    user = result_set.created_by

    # Try to copy from user's timed result
    try:
        timed = ResultSet.objects.get(
            race=race,
            created_by=user,
            source=ResultSet.Source.TIMED
        )
        copy_entries(timed, result_set)
        return
    except ResultSet.DoesNotExist:
        pass

    # Else blank
    create_blank_entries(result_set)

#----------------------------------------------------------#

def populate_manual_position(result_set):
    race = result_set.race
    user = result_set.created_by

    # 1️⃣ Manual time
    try:
        manual_time = ResultSet.objects.get(
            race=race,
            created_by=user,
            source=ResultSet.Source.MANUAL_TIME
        )
        copy_entries(manual_time, result_set)
        return
    except ResultSet.DoesNotExist:
        pass

    # 2️⃣ Timed
    try:
        timed = ResultSet.objects.get(
            race=race,
            created_by=user,
            source=ResultSet.Source.TIMED
        )
        copy_entries(timed, result_set)
        return
    except ResultSet.DoesNotExist:
        pass

    # 3️⃣ Blank
    create_blank_entries(result_set)

#----------------------------------------------------------#

def create_blank_entries(result_set):
    entries = RaceEntry.objects.filter(race=result_set.race)

    for e in entries:
        ResultSetEntry.objects.create(
            result_set=result_set,
            race_entry=e
        )

#----------------------------------------------------------#

def copy_entries(source, target):
    for entry in source.entries.all():
        ResultSetEntry.objects.create(
            result_set=target,
            race_entry=entry.race_entry,
            laps=entry.laps,
            elapsed_seconds=entry.elapsed_seconds,
            finish_position=entry.finish_position,
            corrected_seconds=entry.corrected_seconds,
        )

#----------------------------------------------------------#