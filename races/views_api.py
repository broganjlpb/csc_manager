from django.http import JsonResponse
from races.services import build_race_state


def live_race_state(request, race_id):
    attempt = request.GET.get("attempt")
    attempt = int(attempt) if attempt else None

    state = build_race_state(race_id, attempt)
    return JsonResponse(state)
