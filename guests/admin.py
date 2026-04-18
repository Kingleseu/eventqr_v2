# config/guests/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Invite, Table, InvitationStatus


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre_de_places", "event", "invites_count")
    list_filter = ("event",)
    search_fields = ("numero", "event__name")

    def invites_count(self, obj):
        return obj.invites.count()
    invites_count.short_description = "Nb d'invites"


def mark_present(modeladmin, request, queryset):
    updated = queryset.update(present=True)
    modeladmin.message_user(request, f"{updated} invite(s) marque(s) present(s).")
mark_present.short_description = "Marquer comme present"


def mark_absent(modeladmin, request, queryset):
    updated = queryset.update(present=False)
    modeladmin.message_user(request, f"{updated} invite(s) marque(s) absent(s).")
mark_absent.short_description = "Marquer comme absent"


def set_status_sent(modeladmin, request, queryset):
    updated = queryset.update(status=InvitationStatus.SENT)
    modeladmin.message_user(request, f"Statut mis a 'Envoyee' pour {updated} invite(s).")
set_status_sent.short_description = "Statut 'Envoyee'"


def set_status_confirmed(modeladmin, request, queryset):
    updated = queryset.update(status=InvitationStatus.CONFIRMED)
    modeladmin.message_user(request, f"Statut mis a 'Confirmee' pour {updated} invite(s).")
set_status_confirmed.short_description = "Statut 'Confirmee'"


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "nom", "prenom", "tele", "event", "table",
        "present", "status", "created_at",
    )
    list_filter = ("event", "present", "status", "table")
    search_fields = ("nom", "prenom", "tele", "code", "table__numero", "event__name")
    readonly_fields = ("qr_code_preview", "code", "created_at", "date_scanned")

    fieldsets = (
        ("Evenement & Table", {
            "fields": ("event", "table")
        }),
        ("Identite", {
            "fields": ("nom", "prenom", "tele")
        }),
        ("Invitation", {
            "fields": ("status", "present", "scanned", "date_scanned")
        }),
        ("Code & QR", {
            "fields": ("code", "qr_code", "qr_code_preview")
        }),
        ("Metadonnees", {
            "fields": ("user", "created_at")
        }),
    )

    actions = [mark_present, mark_absent, set_status_sent, set_status_confirmed]

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" alt="QR" style="height:120px;border:1px solid #eee;padding:4px;border-radius:6px;" />',
                obj.qr_code.url
            )
        return "-"
    qr_code_preview.short_description = "Apercu QR"
