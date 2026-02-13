from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from .models import BoatType, RegisteredBoat, League
from .forms import BoatTypeForm, RegisteredBoatForm, LeagueForm
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin

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