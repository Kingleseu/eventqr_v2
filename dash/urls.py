# config/dash/urls.py
from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),

    # Création rapide (boutons du bandeau)
    path("events/new/guests/", views.event_new_guests, name="event_new_guests"),
    path("events/new/retreat/", views.event_new_retreat, name="event_new_retreat"),

    # Actions depuis la carte (modale + suppression)
    path("events/<int:pk>/update/", views.event_update, name="event_update"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
]
