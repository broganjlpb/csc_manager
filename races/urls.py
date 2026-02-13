from django.urls import path
from .views import BoatTypeCreateView, BoatTypeUpdateView, BoatTypeListView
from .views import RegisteredBoatListView, RegisteredBoatCreateView, RegisteredBoatUpdateView,LeagueListView, LeagueCreateView, LeagueUpdateView

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
]

