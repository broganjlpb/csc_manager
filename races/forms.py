from django import forms
from .models import BoatType, RegisteredBoat, League, RaceEntry, Race, Event
from members.models import Member
from django.core.exceptions import ValidationError
from django.db import models


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

class RaceEntryForm(forms.ModelForm):
    class Meta:
        model = RaceEntry
        fields = ["helm", "crew", "boat", "py_used"]

    def __init__(self, *args, race=None, **kwargs):
        self.race = race
        super().__init__(*args, **kwargs)
        # alphabetical by alias
        self.fields["helm"].queryset = Member.objects.order_by("username")
        self.fields["crew"].queryset = Member.objects.order_by("username")

        self.fields["helm"].label_from_instance = lambda obj: obj.username
        self.fields["crew"].label_from_instance = lambda obj: obj.username

        self.fields["boat"].queryset = RegisteredBoat.objects.select_related("boat_type")

        def clean(self):
            cleaned = super().clean()

            helm = cleaned.get("helm")
            crew = cleaned.get("crew")
            boat = cleaned.get("boat")

            if not self.race:
                return cleaned

            # person already sailing?
            if helm and RaceEntry.objects.filter(race=self.race).filter(
                models.Q(helm=helm) | models.Q(crew=helm)
            ).exists():
                raise ValidationError({"helm": "This person is already sailing in this race."})

            if crew and RaceEntry.objects.filter(race=self.race).filter(
                models.Q(helm=crew) | models.Q(crew=crew)
            ).exists():
                raise ValidationError({"crew": "This person is already sailing in this race."})

            # boat already used?
            if boat and RaceEntry.objects.filter(race=self.race, boat=boat).exists():
                raise ValidationError({"boat": "This boat is already entered in the race."})

            return cleaned




class RaceCreateForm(forms.Form):
    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )

    league = forms.ModelChoiceField(queryset=None)
    race_officer = forms.ModelChoiceField(queryset=None)
    assistant_race_officer = forms.ModelChoiceField(
        queryset=None, required=False
    )

    def __init__(self, *args, **kwargs):
        from members.models import Member
        from .models import League

        super().__init__(*args, **kwargs)

        self.fields["league"].queryset = League.objects.all()
        self.fields["race_officer"].queryset = Member.objects.all()
        self.fields["assistant_race_officer"].queryset = Member.objects.all()