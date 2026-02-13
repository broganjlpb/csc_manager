from django import forms
from .models import BoatType, RegisteredBoat, League


class BoatTypeForm(forms.ModelForm):
    class Meta:
        model = BoatType
        fields = "__all__"


class RegisteredBoatForm(forms.ModelForm):
    class Meta:
        model = RegisteredBoat
        fields = "__all__"

class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        fields = "__all__"
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea()
        }