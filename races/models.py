from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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