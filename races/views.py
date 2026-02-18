from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from .models import BoatType, RegisteredBoat, League, Race, RaceEntry, RaceResult, Event, Race, RaceEvent, ResultSet, ResultSetEntry
from members.models import Member
from .forms import BoatTypeForm, RegisteredBoatForm, LeagueForm, RaceEntryForm, RaceEntry, RaceCreateForm, Race
from django.utils import timezone
from django.db.models import Exists, OuterRef
from django.contrib.auth.mixins import PermissionRequiredMixin
from django import forms
from django.views.decorators.http import require_http_methods
from django.db.models import F, Count, Q
from .services import calculate_points, corrected_time
from .services import calculate_league_table, format_seconds, build_manual_time_preview
from django.utils.timezone import now
from django.contrib import messages
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

from races.models import Race, RaceEntry, ResultSet, ResultSetEntry
from races.services import build_race_state, corrected_time, format_seconds 
from races.services import get_or_create_user_resultset, calculate_points




class BoatTypeListView(ListView):
    model = BoatType
    template_name = "races/boattype_list.html"
    context_object_name = "boats"
    ordering = ["name"]
#----------------------------------------------------------#

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
#----------------------------------------------------------#    
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
    
#----------------------------------------------------------# 
class RegisteredBoatListView(ListView):
    model = RegisteredBoat
    template_name = "races/registeredboat_list.html"
    context_object_name = "registeredboats"
    ordering = ["sail_number"]
#----------------------------------------------------------#

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

#----------------------------------------------------------#   
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

#----------------------------------------------------------#
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

#----------------------------------------------------------#
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

#----------------------------------------------------------#
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

#----------------------------------------------------------#   
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

#----------------------------------------------------------#
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

#----------------------------------------------------------#
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

        qs = qs.annotate(
            has_events=Exists(
                # RaceEvent.objects.filter(race=OuterRef("pk"))
                RaceEvent.objects.filter(
                    race=OuterRef("pk"),
                    event_type="start"
                )
            )
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["leagues"] = League.objects.order_by("name")
        context["selected_league"] = self.request.GET.get("league", "all")
        context["selected_status"] = self.request.GET.get("status", "all")

        return context
#----------------------------------------------------------#

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
#----------------------------------------------------------#

def boat_py(request, pk):

    boat = RegisteredBoat.objects.select_related("boat_type").get(pk=pk)
    return JsonResponse({"py": boat.boat_type.py})
#----------------------------------------------------------#

def delete_entry(request, race_pk, entry_pk):
    entry = get_object_or_404(RaceEntry, pk=entry_pk, race_id=race_pk)
    entry.delete()
    return redirect("race-entries", pk=race_pk)
#----------------------------------------------------------#

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
#----------------------------------------------------------#

def reopen_results(request, pk):
    race = get_object_or_404(Race, pk=pk)
    race.status = Race.RaceStatus.OPEN
    race.save()
    return redirect("race-results-manual", pk=pk)
#----------------------------------------------------------#

def league_table(request, pk):
    league = get_object_or_404(League, pk=pk)

    table = calculate_league_table(league)

    return render(request, "races/league_table.html", {
        "league": league,
        "table": table,
    })
#----------------------------------------------------------#

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
#----------------------------------------------------------#

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
#----------------------------------------------------------#

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
#----------------------------------------------------------#

def live_race_page(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    return render(request, "races/live.html", {"race": race})

#----------------------------------------------------------#

def timed_results_edit(request, race_id):

    result_set_id = request.GET.get("result_set")
    result_set = get_object_or_404(ResultSet, pk=result_set_id)

    if result_set.state == ResultSet.State.PUBLISHED:
        messages.error(request, "Cannot edit a published result set.")
        return redirect("race-results-timed", race_id=race_id)

    entries = result_set.entries.select_related(
        "race_entry__boat",
        "race_entry__helm"
    )

    if request.method == "POST":

        for row in entries:
            laps = request.POST.get(f"laps_{row.id}")
            elapsed = request.POST.get(f"elapsed_{row.id}")

            row.laps = int(laps) if laps else None
            row.elapsed_seconds = int(elapsed) if elapsed else None
            row.save()

        messages.success(request, "Timed result set updated.")
        return redirect("race-results-timed",
                        race_id=race_id,
                        )

    return render(request, "races/timed_results_edit.html", {
        "race": result_set.race,
        "result_set": result_set,
        "entries": entries,
    })

#----------------------------------------------------------#

def manual_results(request, pk):
    race = get_object_or_404(Race, pk=pk)
    user = request.user

    result_set, created = ResultSet.objects.get_or_create(
        race=race,
        created_by=user,
        source=ResultSet.Source.MANUAL_POSITION,
    )

    # -------------------------------------------------
    # Populate defaults if new
    # -------------------------------------------------
    if created:
        base_set = ResultSet.objects.filter(
            race=race,
            created_by=user,
            source=ResultSet.Source.MANUAL_TIME
        ).first()

        if not base_set:
            base_set = ResultSet.objects.filter(
                race=race,
                created_by=user,
                source=ResultSet.Source.TIMED
            ).first()

        if base_set:
            for entry in base_set.entries.all():
                ResultSetEntry.objects.create(
                    result_set=result_set,
                    race_entry=entry.race_entry,
                    finish_position=entry.finish_position,
                    tied=getattr(entry, "tied", False),
                )
        else:
            for e in race.entries.all():
                ResultSetEntry.objects.create(
                    result_set=result_set,
                    race_entry=e
                )

    entries = list(
        result_set.entries
        .select_related("race_entry__boat", "race_entry__helm")
        .order_by("finish_position", "id")
    )

    preview = None

    # -------------------------------------------------
    # POST
    # -------------------------------------------------
    if request.method == "POST":
        action = request.POST.get("action")

        # Save positions and ties
        for row in entries:
            pos = request.POST.get(f"pos_{row.id}")
            row.finish_position = int(pos) if pos else None
            row.tied = request.POST.get(f"tie_{row.id}") == "on"
            row.save()

        # Reload sorted after save
        entries = list(
            result_set.entries
            .select_related("race_entry__boat", "race_entry__helm")
            .order_by("finish_position", "id")
        )

        if action == "save":
            result_set.state = ResultSet.State.SAVED
            result_set.save()
            messages.success(request, "Manual positions saved.")
            # return redirect("race-results-manual", pk=race.pk)
            return redirect("select-result-set", race_id=race.pk)

        if action == "preview":

            preview = []

            display_position = 0
            skip = 0

            for index, row in enumerate(entries, start=1):

                if index == 1:
                    display_position = 1
                else:
                    if row.tied:
                        skip += 1
                    else:
                        display_position = display_position + 1 + skip
                        skip = 0

                preview.append({
                    "row": row,
                    "position": display_position,
                    "points": calculate_points(display_position)
                })
    # print("VIEW REACHED")
    return render(request, "races/manual_results.html", {
        "race": race,
        "result_set": result_set,
        "entries": entries,
        "preview": preview,
    })

#----------------------------------------------------------#

def manual_time_results(request, race_id):

    race = get_object_or_404(Race, pk=race_id)

    result_set = get_or_create_user_resultset(
        race,
        request.user,
        ResultSet.Source.MANUAL_TIME
    )

    # Always drive form from RaceEntry
    entries = list(
        race.entries.select_related("boat", "helm")
    )

    preview = None

    # -------------------------------------------------
    # INITIAL GET → LOAD SAVED DATA INTO FORM
    # -------------------------------------------------
    if request.method == "GET":

        saved_entries = {
            e.race_entry_id: e
            for e in result_set.entries.all()
        }

        for e in entries:

            saved = saved_entries.get(e.id)

            if saved:
                e.laps = saved.laps
                e.elapsed_seconds = saved.elapsed_seconds
            else:
                e.laps = None
                e.elapsed_seconds = None

            if e.elapsed_seconds:
                e.h = e.elapsed_seconds // 3600
                e.m = (e.elapsed_seconds % 3600) // 60
                e.s = e.elapsed_seconds % 60
            else:
                e.h = e.m = e.s = ""

        # AUTO BUILD PREVIEW IF SAVED DATA EXISTS
        valid = [
            e for e in entries
            if e.laps and e.elapsed_seconds
        ]

        if valid:
            preview = build_manual_time_preview(valid)

    # -------------------------------------------------
    # POST → PREVIEW OR SAVE
    # -------------------------------------------------
    if request.method == "POST":

        action = request.POST.get("action")

        valid_entries = []

        for e in entries:

            laps = request.POST.get(f"laps_{e.id}")
            h = request.POST.get(f"h_{e.id}") or 0
            m = request.POST.get(f"m_{e.id}") or 0
            s = request.POST.get(f"s_{e.id}") or 0

            total = int(h) * 3600 + int(m) * 60 + int(s)

            e.laps = int(laps) if laps else None
            e.elapsed_seconds = total if total > 0 else None

            if e.elapsed_seconds:
                e.h = e.elapsed_seconds // 3600
                e.m = (e.elapsed_seconds % 3600) // 60
                e.s = e.elapsed_seconds % 60
            else:
                e.h = e.m = e.s = ""

            if e.laps and e.elapsed_seconds:
                valid_entries.append(e)

        if valid_entries:
            preview = build_manual_time_preview(valid_entries)

        # SAVE RESULT SET
        if action == "save" and preview:

            result_set.entries.all().delete()

            for row in preview:

                ResultSetEntry.objects.create(
                    result_set=result_set,
                    race_entry=row["entry"],
                    laps=row["entry"].laps,
                    elapsed_seconds=row["entry"].elapsed_seconds,
                    corrected_seconds=row["corrected_raw"],
                    finish_position=row["position"],
                )

            result_set.state = ResultSet.State.SAVED
            result_set.save()

            messages.success(request, "Manual timed results saved.")
            # return redirect("race-results-manual-time", race_id=race.id)
            return redirect("select-result-set", race_id=race.id)


    return render(request, "races/manual_time_results.html", {
        "race": race,
        "entries": entries,
        "preview": preview,
    })

#----------------------------------------------------------#

def timed_results(request, race_id):

    race = get_object_or_404(Race, pk=race_id)

    # Optional: view existing result set
    result_set_id = request.GET.get("result_set")
    result_set = None
    preview = None

    # ------------------------------------------
    # VIEW EXISTING RESULT SET
    # ------------------------------------------
    if result_set_id:
        result_set = get_object_or_404(ResultSet, pk=result_set_id, race=race)

        entries = result_set.entries.select_related(
            "race_entry__boat",
            "race_entry__helm"
        ).order_by("finish_position")

        preview = []

        for row in entries:
            preview.append({
                "entry_id": row.race_entry_id,
                "helm": row.race_entry.helm.username,
                "sail": row.race_entry.boat.sail_number,
                "laps": row.laps,
                "elapsed": row.elapsed_seconds,
                "corrected": row.corrected_seconds,
                "position": row.finish_position,
            })

        return render(request, "races/timed_results.html", {
            "race": race,
            "preview": preview,
            "result_set": result_set,
            "state": None,
            "attempt_numbers": None,
        })

    # ------------------------------------------
    # BUILD FROM EVENT LOG
    # ------------------------------------------

    attempt = request.GET.get("attempt")
    attempt = int(attempt) if attempt else None

    state = build_race_state(race.id, attempt=attempt)
    attempt_numbers = range(1, state["total_attempts"] + 1)

    boats = list(state["boats"].values())

    valid = [
        b for b in boats
        if b["laps"] and b["last"]
    ]

    if valid:
        max_laps = max(b["laps"] for b in valid)

        ranked = sorted(
            valid,
            key=lambda b: (
                (b["last"] * (max_laps / b["laps"]) * 1000 / b["py"])
                if b["py"] else 999999
            )
        )

        preview = []

        for pos, b in enumerate(ranked, 1):

            corrected = (
                b["last"] * (max_laps / b["laps"]) * 1000 / b["py"]
                if b["py"] else None
            )

            preview.append({
                "entry_id": b["entry_id"],
                "helm": b["helm"],
                "sail": b["sail"],
                "laps": b["laps"],
                "elapsed": b["last"],
                "corrected": corrected,
                "position": pos,
            })

    # ------------------------------------------
    # SAVE RESULT SET
    # ------------------------------------------

    if request.method == "POST" and preview:

        result_set, created = ResultSet.objects.get_or_create(
            race=race,
            source=ResultSet.Source.TIMED,
            created_by=request.user,
            defaults={
                "state": ResultSet.State.SAVED
            }
        )

        # Always clear existing entries (safe)
        result_set.entries.all().delete()

        for row in preview:
            ResultSetEntry.objects.create(
                result_set=result_set,
                race_entry_id=row["entry_id"],
                laps=row["laps"],
                elapsed_seconds=row["elapsed"],
                corrected_seconds=row["corrected"],
                finish_position=row["position"],
            )

        result_set.state = ResultSet.State.SAVED
        result_set.save()

        if created:
            messages.success(request, "Timed result set created.")
        else:
            messages.info(request, "Timed result set updated.")

        # 🚀 THIS is the important change
        return redirect("select-result-set", race_id=race.id)


    return render(request, "races/timed_results.html", {
        "race": race,
        "state": state,
        "preview": preview,
        "attempt_numbers": attempt_numbers,
        "result_set": None,
    })


def select_result_set(request, race_id):
    race = get_object_or_404(Race, pk=race_id)

    result_sets = (
        ResultSet.objects
        .filter(race=race)
        .select_related("created_by")
        .order_by("-created_at")
    )

    my_sets = result_sets.filter(created_by=request.user)
    other_sets = result_sets.exclude(created_by=request.user)

    published = result_sets.filter(
        state=ResultSet.State.PUBLISHED
    ).first()

    return render(request, "races/select_result_set.html", {
        "race": race,
        "my_sets": my_sets,
        "other_sets": other_sets,
        "published": published,
    })

#----------------------------------------------------------#

def publish_result_set(request, result_set_id):

    rs = get_object_or_404(ResultSet, pk=result_set_id)

    # Unpublish existing
    ResultSet.objects.filter(
        race=rs.race,
        state=ResultSet.State.PUBLISHED
    ).update(state=ResultSet.State.SAVED)

    rs.state = ResultSet.State.PUBLISHED
    rs.published_at = timezone.now()
    rs.save()

    messages.success(request, "Result set published.")

    return redirect("select-result-set", race_id=rs.race.id)

#----------------------------------------------------------#