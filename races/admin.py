from django.contrib import admin
from .models import BoatType, RegisteredBoat, League, RaceEntry,Race,RaceResult,Event,RaceEvent, ResultSet, ResultSetEntry

# Register your models here.


@admin.register(BoatType)
class BoatTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "py")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(RegisteredBoat)
class RegisteredBoatAdmin(admin.ModelAdmin):
    list_display = ("sail_number", "boat_type")
    search_fields = ("sail_number",)
    ordering = ("sail_number",)

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "date_from", "date_to")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(RaceEntry)
class RaceEntryAdmin(admin.ModelAdmin):
    list_display = ("race", "helm", "crew", "boat", "boat_type_name", "py_used",)
    search_fields = ("race",)
    ordering = ("race",)

@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ("event", "league", "race_officer", "assistant_race_officer", )
    search_fields = ("event",)
    ordering = ("event",)

@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ("entry", "position", "status","points_override", )
    search_fields = ("entry","position",)
    ordering = ("entry","position",)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("start_datetime", "type", "created_by", "created_at", "is_active")
    search_fields = ("start_datetime", "type")
    ordering = ("start_datetime",)

@admin.register(RaceEvent)
class RaceEventAdmin(admin.ModelAdmin):
    list_display = ("race", "device_id", "sequence", "event_type", "race_entry","created_at")
    search_fields = ("race", "sequence")
    ordering = ("race", "sequence")

@admin.register(ResultSet)
class ResultSetAdmin(admin.ModelAdmin):
    list_display = ("race", "source", "created_by", "created_at", "state","published_at")
    search_fields = ("race", "source", "state")
    ordering = ("race", "state")

@admin.register(ResultSetEntry)
class ResultSetEntryAdmin(admin.ModelAdmin):
    list_display = ("result_set", "race_entry", "laps", "elapsed_seconds", "finish_position","corrected_seconds")
    search_fields = ("result_set", "race_entry")
    ordering = ("result_set", "race_entry")