from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class BoatType(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    py = models.IntegerField(
        "Portsmouth Yardstick",
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(2000),
        ],
    )

    def __str__(self):
        return f'{self.name} ({self.py})'
        # return self.name
    
class RegisteredBoat(models.Model):
    sail_number = models.CharField(max_length=20)
    boat_type = models.ForeignKey(BoatType,on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.sail_number} {self.boat_type}'


class League(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200, blank=True)
    date_from = models.DateField(help_text='The first date a race can be added to this league')
    date_to = models.DateField(help_text='The last date a race can be added to this league')

    def __str__(self):
        return self.name
    
class Event(models.Model):

    class EventType(models.TextChoices):
        RACE = "race", "Race"
        MEETING = "meeting", "Meeting"
        WORKPARTY = "workparty", "Work Party"

    start_datetime = models.DateTimeField()
    type = models.CharField(max_length=20, choices=EventType.choices)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="events_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_type_display()} @ {self.start_datetime}"
    
class Race(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)

    league = models.ForeignKey(
        "races.League",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="races",
    )

    race_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="races_as_ro",
    )

    assistant_race_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="races_as_aro",
    )

    class RaceStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        RUNNING = "running", "Running"
        FINISHED = "finished", "Finished"
        VERIFIED = "verified", "Verified"
        LOCKED = "locked", "Locked"

    status = models.CharField(
        max_length=20,
        choices=RaceStatus.choices,
        default=RaceStatus.DRAFT,
    )

    def __str__(self):
        return f"Race on {self.event.start_datetime}"
    
class Race(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)

    league = models.ForeignKey(
        "races.League",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="races",
    )

    race_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="races_as_ro",
    )

    assistant_race_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="races_as_aro",
    )

    class RaceStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        RUNNING = "running", "Running"
        FINISHED = "finished", "Finished"
        VERIFIED = "verified", "Verified"
        LOCKED = "locked", "Locked"

    status = models.CharField(
        max_length=20,
        choices=RaceStatus.choices,
        default=RaceStatus.DRAFT,
    )

    def __str__(self):
        return f"Race on {self.event.start_datetime}"
    
class RaceEntry(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="entries")

    helm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="races_as_helm",
    )

    crew = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="races_as_crew",
    )

    boat = models.ForeignKey(
        "races.RegisteredBoat",
        on_delete=models.PROTECT,
    )

    # snapshot fields ⭐⭐⭐
    boat_type_name = models.CharField(max_length=200)
    py_used = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["race", "boat"], name="unique_boat_per_race"),
            models.UniqueConstraint(fields=["race", "helm"], name="unique_helm_per_race"),
        ]

    def __str__(self):
        return f"{self.boat} – {self.helm}"

class RaceResult(models.Model):
    class ResultStatus(models.TextChoices):
        OK = "ok", "Finished"
        DNF = "dnf", "DNF"
        DSQ = "dsq", "DSQ"
        DNS = "dns", "DNS"

    entry = models.OneToOneField(
        RaceEntry,
        on_delete=models.CASCADE,
        related_name="result"
    )

    position = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=ResultStatus.choices,
        default=ResultStatus.OK,
    )

    points_override = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.entry} – {self.status}"

