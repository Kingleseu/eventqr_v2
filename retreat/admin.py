from django.contrib import admin
from .models import (
    Parametrage, Testimony, LogAction,
    Responsable, Chambre, Atelier, Participant,
    OTPVerification, BilletGlobalFiles, Notification
)

@admin.register(Parametrage)
class ParametrageAdmin(admin.ModelAdmin):
    list_display = ("inscription_active", "maintenance_mode", "date_modif")

@admin.register(Testimony)
class TestimonyAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "validated", "date_submitted")
    list_filter = ("validated", "color")
    search_fields = ("name", "message")

@admin.register(LogAction)
class LogActionAdmin(admin.ModelAdmin):
    list_display = ("date_action", "user", "action_type", "action")
    list_filter = ("action_type",)
    search_fields = ("action", "details", "user__username")

@admin.register(Responsable)
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "sexe", "age", "atelier")
    list_filter = ("sexe", "atelier")
    search_fields = ("prenom", "nom")

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ("nom", "event", "sexe", "capacite")
    list_filter = ("event", "sexe")
    search_fields = ("nom", "event__name")

@admin.register(Atelier)
class AtelierAdmin(admin.ModelAdmin):
    list_display = ("numero", "event")
    list_filter = ("event",)
    search_fields = ("numero", "event__name")

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "event", "sexe", "present", "paiement_valide")
    list_filter = ("event", "sexe", "present", "paiement_valide")
    search_fields = ("prenom", "nom", "email", "telephone")

admin.site.register(OTPVerification)
admin.site.register(BilletGlobalFiles)
admin.site.register(Notification)
