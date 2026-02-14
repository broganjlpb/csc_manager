from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from .models import BoatType, RegisteredBoat, League, Race, RaceEntry, RaceResult, Event
from members.models import Member
from .forms import BoatTypeForm, RegisteredBoatForm, LeagueForm, RaceEntryForm, RaceEntry, RaceCreateForm
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin
from django import forms
from django.views.decorators.http import require_http_methods

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

class RaceListView(ListView):
    model = Race
    template_name = "races/race_list.html"
    context_object_name = "races"
    ordering = ["-event__start_datetime"]

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

@require_http_methods(["GET", "POST"])
def manual_results(request, pk):
    race = get_object_or_404(Race, pk=pk)

    if request.method == "POST":
        order = request.POST.getlist("order[]")

        for position, entry_id in enumerate(order, start=1):
            RaceEntry.objects.filter(pk=entry_id, race=race).update(
                finish_position=position
            )

        return redirect("races-list")

    entries = race.entries.select_related("helm", "boat").order_by("finish_position", "id")


    return render(request, "races/manual_results.html", {
        "race": race,
        "entries": entries,
    })


