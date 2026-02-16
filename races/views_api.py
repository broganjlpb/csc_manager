from django.http import JsonResponse
from races.services import build_race_state


def live_race_state(request, race_id):
    state = build_race_state(race_id)
    return JsonResponse(state)
