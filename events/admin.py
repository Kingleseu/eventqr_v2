from django.contrib import admin
from .models import Event, Table


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "organization", "starts_at", "is_active")
    list_filter = ("event_type", "organization", "is_active")
    search_fields = ("name", "venue", "organization__name")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("label", "event", "capacity")
    list_filter = ("event",)
    search_fields = ("label", "event__name")