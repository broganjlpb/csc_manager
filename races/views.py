from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from .models import BoatType, RegisteredBoat, League, Race, RaceEntry, RaceResult, Event, Race, RaceEvent
from members.models import Member
from .forms import BoatTypeForm, RegisteredBoatForm, LeagueForm, RaceEntryForm, RaceEntry, RaceCreateForm
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin
from django import forms
from django.views.decorators.http import require_http_methods
from django.db.models import F, Count, Q
from .services import calculate_points, corrected_time
from .services import calculate_league_table, format_seconds
from django.utils.timezone import now
from django.contrib import messages
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from races.services import build_race_state

from races.models import Race, RaceEntry
from races.services import build_race_state, corrected_time, format_seconds 


class BoatTypeListView(ListView):
    model = BoatType
    template_name = "races/boattype_list.html"
    context_object_name = "boats"
    ordering = ["name"]

class BoatTypeCreateView(CreateView):
    model = BoatType
    form_class = BoatTypeForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("boattype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Boat Type"
        context["submit_text"] = "Create"
        context["cancel_url"] = reverse_lazy("boattype-list")
        return context
    
class BoatTypeUpdateView(UpdateView):
    model = BoatType
    form_class = BoatTypeForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("boattype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.object.name}"
        context["submit_text"] = "Save changes"
        context["cancel_url"] = reverse_lazy("boattype-list")
        return context
    
class RegisteredBoatListView(ListView):
    model = RegisteredBoat
    template_name = "races/registeredboat_list.html"
    context_object_name = "registeredboats"
    ordering = ["sail_number"]

class RegisteredBoatCreateView(CreateView):
    model = RegisteredBoat
    form_class = RegisteredBoatForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("registered-boats-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Register a Boat"
        context["submit_text"] = "Create"
        context["cancel_url"] = reverse_lazy("registered-boats-list")
        return context
    
class RegisteredBoatUpdateView(UpdateView):
    model = RegisteredBoat
    form_class = RegisteredBoatForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("registered-boats-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.object.sail_number}"
        context["submit_text"] = "Save changes"
        context["cancel_url"] = reverse_lazy("registered-boats-list")
        return context
    
class LeagueListView(ListView):
    model = League
    template_name = "races/leagues_list.html"
    context_object_name = "leagues"
    ordering = ["date_from"]

    def get_queryset(self):
        qs = super().get_queryset()

        current = self.request.GET.get("current")

        if current:
            today = timezone.now().date()
            qs = qs.filter(date_from__lte=today, date_to__gte=today)

        return qs

class LeagueCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "races.add_league"
    permission_denied_message = "You cannot add leagues."
    raise_exception = True
    model = League
    form_class = LeagueForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("leagues-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add a League"
        context["submit_text"] = "Create"
        context["cancel_url"] = reverse_lazy("leagues-list")
        return context
    
class LeagueUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "races.change_league"
    permission_denied_message = "You cannot edit leagues."
    raise_exception = True
    model = League
    form_class = LeagueForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("leagues-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.object.name}"
        context["submit_text"] = "Save changes"
        context["cancel_url"] = reverse_lazy("leagues-list")
        return context
    
class RaceEntryListView(DetailView):
    model = Race
    template_name = "races/race_entries.html"
    context_object_name = "race"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entries"] = self.object.entries.select_related("helm", "crew", "boat")
        context["form"] = RaceEntryForm(race=self.object)

        context["existing_helms"] = list(
            self.object.entries.values_list("helm_id", flat=True)
        )
        context["existing_crew"] = list(
            self.object.entries.values_list("crew_id", flat=True)
        )

        context["existing_boats"] = list(
            self.object.entries.values_list("boat_id", flat=True)
        )

        return context

class RaceCreateView(FormView):
    template_name = "forms/form_page.html"
    form_class = RaceCreateForm

    def form_valid(self, form):
        event = Event.objects.create(
            start_datetime=form.cleaned_data["start_datetime"],
            type=Event.EventType.RACE,
            created_by=self.request.user,
        )

        race = Race.objects.create(
            event=event,
            league=form.cleaned_data["league"],
            race_officer=form.cleaned_data["race_officer"],
            assistant_race_officer=form.cleaned_data["assistant_race_officer"],
        )

        return redirect("race-entries", pk=race.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Race"
        context["submit_text"] = "Create"
        context["cancel_url"] = reverse("races-list")
        return context

# -event__start_datetime
class RaceListView(ListView):
    model = Race
    template_name = "races/race_list.html"
    context_object_name = "races"
    ordering = ["-event__start_datetime"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("league")

        league_id = self.request.GET.get("league")
        status = self.request.GET.get("status")

        if league_id and league_id != "all":
            qs = qs.filter(league_id=league_id)

        if status and status != "all":
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["leagues"] = League.objects.order_by("name")
        context["selected_league"] = self.request.GET.get("league", "all")
        context["selected_status"] = self.request.GET.get("status", "all")

        return context


def add_entry(request, pk):
    race = get_object_or_404(Race, pk=pk)

    if request.method == "POST":
        form = RaceEntryForm(request.POST, race=race)

        if form.is_valid():
            entry = form.save(commit=False)
            entry.race = race

            entry.boat_type_name = entry.boat.boat_type.name
            if not entry.py_used:
                entry.py_used = entry.boat.boat_type.py

            entry.save()
            return redirect("race-entries", pk=pk)

    else:
        form = RaceEntryForm(race=race)

    return render(request, "races/race_entries.html", {
        "race": race,
        "form": form,
        "entries": race.entries.select_related("helm", "crew", "boat"),
    })


def boat_py(request, pk):

    boat = RegisteredBoat.objects.select_related("boat_type").get(pk=pk)
    return JsonResponse({"py": boat.boat_type.py})

def delete_entry(request, race_pk, entry_pk):
    entry = get_object_or_404(RaceEntry, pk=entry_pk, race_id=race_pk)
    entry.delete()
    return redirect("race-entries", pk=race_pk)

def edit_entry(request, race_pk, entry_pk):
    race = get_object_or_404(Race, pk=race_pk)
    entry = get_object_or_404(RaceEntry, pk=entry_pk, race=race)

    if request.method == "POST":
        form = RaceEntryForm(request.POST, instance=entry, race=race)

        if form.is_valid():
            form.save()
            return redirect("race-entries", pk=race_pk)

    else:
        form = RaceEntryForm(instance=entry, race=race)

    other_entries = race.entries.exclude(pk=entry.pk)
    return render(request, "races/race_entries.html", {
        "race": race,
        "form": form,
        "entries": race.entries.select_related("helm", "crew", "boat"),
        "editing_entry": entry,
        "existing_helms": list(other_entries.values_list("helm_id", flat=True)),
        "existing_crew": list(other_entries.values_list("crew_id", flat=True)),
        "existing_boats": list(other_entries.values_list("boat_id", flat=True)),
    })

def reopen_results(request, pk):
    race = get_object_or_404(Race, pk=pk)
    race.status = Race.RaceStatus.OPEN
    race.save()
    return redirect("race-results-manual", pk=pk)

@require_http_methods(["GET", "POST"])
def manual_results(request, pk):
    race = get_object_or_404(Race, pk=pk)

    if request.method == "POST":
        print(request.POST)
        for entry in race.entries.all():

            pos = request.POST.get(f"position_{entry.id}")
            status = request.POST.get(f"status_{entry.id}")

            if status in ["dnf", "dsq"]:
                entry.result_status = status
                entry.finish_position = None
            else:
                entry.result_status = "finished"
                entry.finish_position = pos

            entry.save()

        # move race forward
        race.status = Race.RaceStatus.FINISHED
        race.save()

        # return redirect("races-list")
        return redirect("race-results-manual", pk=race.pk)


    entries = race.entries.select_related("helm", "boat").order_by(F("finish_position").asc(nulls_last=True),"id")
    for e in entries:
        e.points = calculate_points(e.finish_position)

    return render(request, "races/manual_results.html", {
        "race": race,
        "entries": entries,
    })

def league_table(request, pk):
    league = get_object_or_404(League, pk=pk)

    table = calculate_league_table(league)

    return render(request, "races/league_table.html", {
        "league": league,
        "table": table,
    })

def active_leagues(request):
    today = now().date()

    leagues = (
        League.objects
        .filter(date_from__lte=today, date_to__gte=today)
        .annotate(
            draft_count=Count("races", filter=Q(races__status="draft")),
            open_count=Count("races", filter=Q(races__status="open")),
            running_count=Count("races", filter=Q(races__status="running")),
            finished_count=Count("races", filter=Q(races__status="finished")),
            verified_count=Count("races", filter=Q(races__status="verified")),
            locked_count=Count("races", filter=Q(races__status="locked")),
        )
        .order_by("date_to")
    )

    return render(request, "races/active_leagues.html", {
        "leagues": leagues,
    })


    race = get_object_or_404(Race, pk=pk)
    entries = race.entries.select_related("boat", "helm")

    state = build_race_state(race.id)

    # populate RaceEntry from event history
    for e in entries:
        b = state["boats"].get(e.id)
        if not b:
            continue

        e.laps = b["laps"]
        e.elapsed_seconds = b["last"]

    preview = None

    if request.method == "POST":
        action = request.POST.get("action")

        # 🚨 protection against overwrite
        if race.status in [
            Race.RaceStatus.FINISHED,
            Race.RaceStatus.VERIFIED,
            Race.RaceStatus.LOCKED,
        ] and action in ["preview", "confirm"]:
            messages.error(request, "Results already exist. Use Edit to modify.")
            return redirect("race-results-timed", pk=race.pk)

        # ✅ Always save entered values
        for e in entries:
            laps = request.POST.get(f"laps_{e.id}")

            h = request.POST.get(f"h_{e.id}") or 0
            m = request.POST.get(f"m_{e.id}") or 0
            s = request.POST.get(f"s_{e.id}") or 0

            total = int(h) * 3600 + int(m) * 60 + int(s)

            e.laps = int(laps) if laps else None
            e.elapsed_seconds = total if total > 0 else None

            status = request.POST.get(f"status_{e.id}")
            if status:
                e.result_status = status
            else:
                e.result_status = RaceEntry.ResultStatus.FINISHED

            e.save()


        # 🔹 SAVE ONLY
        if action == "save":
            messages.success(request, "Times saved.")
            return redirect("race-results-timed", pk=race.pk)

        # 🔹 PREVIEW
        if action == "preview":
            
            valid = [
                e for e in entries
                if e.elapsed_seconds and e.laps and e.result_status in [None, "", "finished"]
                # if e.elapsed_seconds and e.laps and e.result_status not in ["dnf", "dsq"]
            ]

            print("VALID: " , valid)

            if valid:
                max_laps = max(e.laps for e in valid)

                ranked = sorted(
                    valid,
                    key=lambda x: corrected_time(
                        x.elapsed_seconds,
                        x.py_used,
                        x.laps,
                        max_laps
                    )
                )

                preview = []

                last_time = None
                position = 0

                for index, e in enumerate(ranked, start=1):
                    ct = corrected_time(
                        e.elapsed_seconds,
                        e.py_used,
                        e.laps,
                        max_laps
                    )

                    if last_time is None:
                        position = 1
                    elif ct > last_time:
                        position = index
                    # else → same position

                    preview.append({
                        "entry": e,
                        "position": position,
                        "corrected": format_seconds(ct),
                    })

                    last_time = ct

        # 🔹 CONFIRM
        if action == "confirm":
            valid = [
                e for e in entries
                if e.elapsed_seconds and e.laps and e.result_status not in ["dnf", "dsq"]
            ]

            if valid:
                max_laps = max(e.laps for e in valid)

                ranked = sorted(
                    valid,
                    key=lambda x: corrected_time(
                        x.elapsed_seconds,
                        x.py_used,
                        x.laps,
                        max_laps
                    )
                )

                for pos, e in enumerate(ranked, start=1):
                    e.finish_position = pos
                    e.save()

            race.status = Race.RaceStatus.FINISHED
            race.save()

            messages.success(request, "Results confirmed.")
            return redirect("race-results-timed", pk=race.pk)



    for e in entries:
        if e.elapsed_seconds:
            e.h = e.elapsed_seconds // 3600
            e.m = (e.elapsed_seconds % 3600) // 60
            e.s = e.elapsed_seconds % 60
        else:
            e.h = e.m = e.s = ""
    
    if race.status == Race.RaceStatus.FINISHED:
        valid = [
            e for e in entries
            if e.elapsed_seconds and e.laps and e.result_status not in ["dnf", "dsq"]
        ]

        if valid:
            max_laps = max(e.laps for e in valid)

            preview = []

            for e in valid:
                preview.append({
                    "entry": e,
                    "position": e.finish_position,
                    "corrected": format_seconds(
                        corrected_time(
                            e.elapsed_seconds,
                            e.py_used,
                            e.laps,
                            max_laps
                        )
                    )
                })

    return render(request, "races/timed_results.html", {
        "race": race,
        "entries": entries,
        "preview": preview,
    })

def timed_results_edit(request, pk):
    race = get_object_or_404(Race, pk=pk)

    race.status = Race.RaceStatus.OPEN
    race.save()

    messages.warning(request, "Race reopened for editing.")

    return redirect("race-results-timed", pk=race.pk)

def race_timer(request, pk):
    race = get_object_or_404(Race, pk=pk)
    entries = race.entries.all()

    if request.method == "POST":
        data = json.loads(request.body)

        for entry_id, info in data.items():
            e = entries.get(pk=entry_id)

            e.laps = info["laps"]

            if info["times"]:
                e.elapsed_seconds = info["times"][-1]

            e.result_status = "finished"
            e.save()

        return JsonResponse({"ok": True})

    return render(request, "races/race_timer.html", {
        "race": race,
        "entries": entries,
    })

@csrf_exempt
def race_event_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)

        race_id = data["race"]
        device_id = data["device_id"]
        sequence = data["sequence"]
        event_type = data["event_type"]
        race_seconds = data.get("race_seconds")
        entry_id = data.get("race_entry")

        entry = None
        if entry_id:
            entry = RaceEntry.objects.get(id=entry_id)

        RaceEvent.objects.create(
            race_id=race_id,
            device_id=device_id,
            sequence=sequence,
            event_type=event_type,
            race_entry=entry,
            race_seconds=race_seconds,
        )

        return JsonResponse({"status": "ok"})

    except IntegrityError:
        # duplicate → safe → treat as success
        return JsonResponse({"status": "duplicate"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def live_race_page(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    return render(request, "races/live.html", {"race": race})


def timed_results(request, pk):
    race = get_object_or_404(Race, pk=pk)
    entries = race.entries.select_related("boat", "helm")

    # ⭐ attempt selection
    attempt = request.GET.get("attempt")
    attempt = int(attempt) if attempt else None

    # ⭐ build from history
    state = build_race_state(race.id, attempt)

    # ⭐ populate RaceEntry from replay
    for e in entries:
        b = state["boats"].get(e.id)
        if not b:
            continue

        e.laps = b["laps"]
        e.elapsed_seconds = b["last"]

    preview = None

    # ==========================================================
    # POST ACTIONS  (UNCHANGED LOGIC)
    # ==========================================================
    if request.method == "POST":
        action = request.POST.get("action")

        if race.status in [
            Race.RaceStatus.FINISHED,
            Race.RaceStatus.VERIFIED,
            Race.RaceStatus.LOCKED,
        ] and action in ["preview", "confirm"]:
            messages.error(request, "Results already exist. Use Edit to modify.")
            return redirect("race-results-timed", pk=race.pk)

        # save edits from form
        for e in entries:
            laps = request.POST.get(f"laps_{e.id}")

            h = request.POST.get(f"h_{e.id}") or 0
            m = request.POST.get(f"m_{e.id}") or 0
            s = request.POST.get(f"s_{e.id}") or 0

            total = int(h) * 3600 + int(m) * 60 + int(s)

            e.laps = int(laps) if laps else None
            e.elapsed_seconds = total if total > 0 else None

            status = request.POST.get(f"status_{e.id}")
            if status:
                e.result_status = status
            else:
                e.result_status = RaceEntry.ResultStatus.FINISHED

            e.save()

        # SAVE ONLY
        if action == "save":
            messages.success(request, "Times saved.")
            return redirect("race-results-timed", pk=race.pk)

        # PREVIEW
        if action == "preview":
            valid = [
                e for e in entries
                if e.elapsed_seconds and e.laps and e.result_status in [None, "", "finished"]
            ]

            if valid:
                max_laps = max(e.laps for e in valid)

                ranked = sorted(
                    valid,
                    key=lambda x: corrected_time(
                        x.elapsed_seconds,
                        x.py_used,
                        x.laps,
                        max_laps
                    )
                )

                preview = []

                last_time = None
                position = 0

                for index, e in enumerate(ranked, start=1):
                    ct = corrected_time(
                        e.elapsed_seconds,
                        e.py_used,
                        e.laps,
                        max_laps
                    )

                    if last_time is None:
                        position = 1
                    elif ct > last_time:
                        position = index

                    preview.append({
                        "entry": e,
                        "position": position,
                        "corrected": format_seconds(ct),
                    })

                    last_time = ct

        # CONFIRM
        if action == "confirm":
            valid = [
                e for e in entries
                if e.elapsed_seconds and e.laps and e.result_status not in ["dnf", "dsq"]
            ]

            if valid:
                max_laps = max(e.laps for e in valid)

                ranked = sorted(
                    valid,
                    key=lambda x: corrected_time(
                        x.elapsed_seconds,
                        x.py_used,
                        x.laps,
                        max_laps
                    )
                )

                for pos, e in enumerate(ranked, start=1):
                    e.finish_position = pos
                    e.save()

            race.status = Race.RaceStatus.FINISHED
            race.save()

            messages.success(request, "Results confirmed.")
            return redirect("race-results-timed", pk=race.pk)

    # ==========================================================
    # format for form display
    # ==========================================================
    for e in entries:
        if e.elapsed_seconds:
            e.h = e.elapsed_seconds // 3600
            e.m = (e.elapsed_seconds % 3600) // 60
            e.s = e.elapsed_seconds % 60
        else:
            e.h = e.m = e.s = ""

    # show official results if finished
    if race.status == Race.RaceStatus.FINISHED:
        valid = [
            e for e in entries
            if e.elapsed_seconds and e.laps and e.result_status not in ["dnf", "dsq"]
        ]

        if valid:
            max_laps = max(e.laps for e in valid)

            preview = []

            for e in valid:
                preview.append({
                    "entry": e,
                    "position": e.finish_position,
                    "corrected": format_seconds(
                        corrected_time(
                            e.elapsed_seconds,
                            e.py_used,
                            e.laps,
                            max_laps
                        )
                    )
                })
    attempt_numbers = list(range(1, state["total_attempts"] + 1))

    return render(request, "races/timed_results.html", {
        "race": race,
        "entries": entries,
        "preview": preview,
        "state": state, 
        "attempt_numbers": attempt_numbers,   # ⭐ needed for attempts UI
    })
