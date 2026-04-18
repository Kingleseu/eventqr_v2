from django.db import models
from core.models import Organization


class EventType(models.TextChoices):
    INVITE = "INVITE", "Invités"
    RETREAT = "RETREAT", "Retraite"


class Event(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True, default="")
    theme = models.CharField(max_length=150, blank=True, default="")
    location_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


class Table(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    label = models.CharField(max_length=50) # ex: "Table 3"
    capacity = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.label} @ {self.event.name}"
