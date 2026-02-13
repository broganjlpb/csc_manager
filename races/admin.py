from django.contrib import admin
from .models import BoatType, RegisteredBoat, League

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