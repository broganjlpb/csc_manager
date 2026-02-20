from django.urls import path
from .views import BoatTypeCreateView, BoatTypeUpdateView, BoatTypeListView, delete_entry, edit_entry, manual_results, reopen_results, league_table, active_leagues, timed_results, timed_results_edit, race_timer, race_event_api, live_race_page, unpublish_result_set
from .views import RegisteredBoatListView, RegisteredBoatCreateView, RegisteredBoatUpdateView,LeagueListView, LeagueCreateView, LeagueUpdateView, RaceEntryListView, RaceCreateView, RaceListView ,add_entry, boat_py, manual_time_results, manual_results, select_result_set, publish_result_set
from .views_api import live_race_state

urlpatterns = [
    path("dashboard", active_leagues, name="dashboard"),
    
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

    path("<int:pk>/results/manual/", manual_results, name="race-results-manual"),
    path("<int:pk>/results/edit/", reopen_results, name="race-results-edit"),

    path("leagues/<int:pk>/table/", league_table, name="league-table"),
    path("leagues/active/", active_leagues, name="active-leagues"),

    # path("<int:pk>/results/timed/", timed_results, name="race-results-timed"),
    path("<int:race_id>/results/timed/", timed_results, name="race-results-timed"),
    path("<int:pk>/results/timed/edit/", timed_results_edit, name="race-results-timed-edit"),

    path("<int:pk>/timer/", race_timer, name="race-timer"),

    path("api/race-event/", race_event_api, name="race_event_api"),

    path("api/race/<int:race_id>/live/", live_race_state),
    path("<int:race_id>/live/", live_race_page, name="race-live"),
    path("<int:race_id>/live/state/", live_race_state, name="live_state"),
    path("races/<int:race_id>/results/manual-time/", manual_time_results, name="race-results-manual-time"),


    path("races/<int:race_id>/results/", select_result_set, name="select-result-set"),
    path("results/<uuid:result_set_id>/publish/", publish_result_set, name="publish-result-set"),

    path("results/<uuid:result_set_id>/publish/",publish_result_set,name="publish-result-set"),
    path("results/<uuid:result_set_id>/unpublish/",unpublish_result_set,name="unpublish-result-set"),
]

