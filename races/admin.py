from django.contrib import admin
from .models import BoatType, RegisteredBoat, League, RaceEntry,Race,RaceResult

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
    list_display = ("race", "helm", "crew", "boat", "boat_type_name", "py_used", "finish_position",)
    search_fields = ("race","finish_position",)
    ordering = ("race","finish_position",)

@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ("event", "league", "race_officer", "assistant_race_officer", "status", )
    search_fields = ("event","status",)
    ordering = ("event","status",)

@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ("entry", "position", "status","points_override", )
    search_fields = ("entry","position",)
    ordering = ("entry","position",)

