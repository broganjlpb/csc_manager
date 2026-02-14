from django.urls import path
from .views import BoatTypeCreateView, BoatTypeUpdateView, BoatTypeListView, delete_entry, edit_entry
from .views import RegisteredBoatListView, RegisteredBoatCreateView, RegisteredBoatUpdateView,LeagueListView, LeagueCreateView, LeagueUpdateView, RaceEntryListView, RaceCreateView, RaceListView ,add_entry, boat_py

urlpatterns = [
    path("boat-types/", BoatTypeListView.as_view(), name="boattype-list"),
    path("boat-types/add/", BoatTypeCreateView.as_view(), name="boattype-add"),
    path("boat-types/<int:pk>/edit/", BoatTypeUpdateView.as_view(), name="boattype-edit"),

    path("registered-boats/", RegisteredBoatListView.as_view(), name="registered-boats-list"),
    path("registered-boats/add/", RegisteredBoatCreateView.as_view(), name="registered-boats-add"),
    path("registered-boats/<int:pk>/edit/", RegisteredBoatUpdateView.as_view(), name="registered-boats-edit"),

    path("leagues/", LeagueListView.as_view(), name="leagues-list"),
    path("leagues/add/", LeagueCreateView.as_view(), name="leagues-add"),
    path("leagues/<int:pk>/edit/", LeagueUpdateView.as_view(), name="leagues-edit"),

    path("", RaceListView.as_view(), name="races-list"),
    path("add/", RaceCreateView.as_view(), name="race-add"),
    path("<int:pk>/entries/", RaceEntryListView.as_view(), name="race-entries"),
    path("<int:pk>/entries/add/", add_entry, name="race-entry-add"),

    path("api/boat/<int:pk>/py/", boat_py, name="boat-py"),
    
    path("<int:race_pk>/entries/<int:entry_pk>/delete/", delete_entry, name="race-entry-delete"),
    path("<int:race_pk>/entries/<int:entry_pk>/edit/", edit_entry, name="race-entry-edit"),
]

