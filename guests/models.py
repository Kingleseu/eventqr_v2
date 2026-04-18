from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

import uuid
import qrcode
from io import BytesIO

from events.models import Event
# --- Default utilisé par d'anciennes migrations ---
# NE PAS RENOMMER ce symbole : la migration 0001 l'importe via
# 'guests.models.generate_qr_token'.
from django.utils.crypto import get_random_string

def generate_qr_token() -> str:
    """
    Génère un token aléatoire de 64 caractères (letters+digits),
    compatible avec CharField(max_length=64).
    Garder ce nom et cet emplacement pour la compatibilité migrations.
    """
    return get_random_string(64)


class InvitationStatus(models.TextChoices):
    PENDING   = "pending",   "En attente"
    SENT      = "sent",      "Envoyée"
    OPENED    = "opened",    "Ouverte"
    CONFIRMED = "confirmed", "Confirmée"
    DECLINED  = "declined",  "Déclinée"
    BOUNCED   = "bounced",   "Email en erreur"


class Table(models.Model):
    """
    Table d’un événement de type 'guests'.
    Un même numéro de table ne peut exister qu’une fois par Event.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tables",
        null=True, blank=True,
    )

    # Pas de limit_choices_to => on valide dans clean()
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="tables",
        null=True, blank=True,
        help_text="Doit être un Event de type 'guests'.",
    )

    numero = models.CharField(max_length=10)
    # Nouveau champ pour le titre/tag de la table (ex: "Table d'Honneur")
    nom = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: 'Table d'Honneur', 'Les Cousins'...")
    color = models.CharField(max_length=7, default="#FFFFFF", help_text="Couleur de fond (Hex).")
    nombre_de_places = models.PositiveIntegerField()

    # Visual Plan Coordinates (Percentages 0-100)
    x_pos = models.FloatField(default=0.0)
    y_pos = models.FloatField(default=0.0)

    # Shape
    class Shape(models.TextChoices):
        ROUND = "round", "Ronde"
        SQUARE = "square", "Carrée"
        RECTANGLE = "rectangle", "Rectangulaire"

    shape = models.CharField(
        max_length=10, 
        choices=Shape.choices, 
        default=Shape.ROUND
    )

    class Meta:
        unique_together = ("event", "numero")
        indexes = [
            models.Index(fields=["event", "numero"]),
        ]

    def clean(self):
        if self.event:
            # On accepte event.event_type OU event.type
            evt_type = getattr(self.event, "event_type", None) or getattr(self.event, "type", None)
            if evt_type != "guests":
                raise ValidationError("Cette table doit appartenir à un événement de type 'guests'.")

    def __str__(self):
        evt = self.event.name if self.event else "—"
        label = self.nom if self.nom else f"Table {self.numero}"
        return f"{label} ({self.nombre_de_places} places) — {evt}"


class Invite(models.Model):
    """
    Invité rattaché à un Event (type 'guests').
    Génère un QR code (PNG) avec nom/prénom + info table.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invites',
        null=True, blank=True,
    )

    # Pas de limit_choices_to => on valide dans clean()
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="invites",
        null=True, blank=True,
        help_text="Doit être un Event de type 'guests'.",
    )

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    # L'email devient optionnel pour ne garder que le téléphone comme saisie principale
    email = models.EmailField(blank=True, null=True)
    tele = models.CharField(max_length=15, blank=True, default="")
    # Identifiant commun pour lier deux invités d'un couple
    couple_id = models.CharField(max_length=36, blank=True, null=True, db_index=True)

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invites',
    )

    # pas unique / nullable pour faciliter les migrations initiales
    code = models.CharField(max_length=36, db_index=True, null=True, blank=True)

    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    present = models.BooleanField(default=False)
    scanned = models.BooleanField(default=False)
    date_scanned = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["event", "nom", "prenom"]),
            models.Index(fields=["code"]),
        ]

    def clean(self):
        # 1) Le bon type d’event
        if self.event:
            evt_type = getattr(self.event, "event_type", None) or getattr(self.event, "type", None)
            if evt_type != "guests":
                raise ValidationError("Cet invité doit appartenir à un événement de type 'guests'.")
        # 2) Cohérence table/event
        if self.table and self.event and self.table.event_id != self.event_id:
            raise ValidationError("La table sélectionnée appartient à un autre événement.")

    def save(self, *args, **kwargs):
        self.full_clean()  # force la validation même hors admin
        return super().save(*args, **kwargs)

    def __str__(self):
        evt = self.event.name if self.event else "—"
        return f"{self.nom} {self.prenom} — {evt}"


# -------- Génération du code + QR auto --------

@receiver(pre_save, sender=Invite)
def ensure_code(sender, instance: Invite, **kwargs):
    if not instance.code:
        instance.code = str(uuid.uuid4())

def _qr_payload(invite: Invite) -> str:
    # On utilise maintenant le string representation de la table ou juste le numero
    # Si la table a un nom, on pourrait vouloir l'afficher dans le QR aussi, 
    # mais pour rester court on garde peut-être le numero + nom court
    if not invite.table:
        table_txt = "Non assignée"
    else:
        # Si nom exist, on l'utilise, sinon numero
        if invite.table.nom:
            table_txt = f"{invite.table.numero} ({invite.table.nom})" 
        else:
            table_txt = invite.table.numero

    return f"Prénom: {invite.prenom} | Nom: {invite.nom} | Table: {table_txt}"

@receiver(post_save, sender=Invite)
def build_qr(sender, instance: Invite, created, **kwargs):
    payload = _qr_payload(instance)
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    filename = f"qr_{instance.pk}.png"
    instance.qr_code.save(filename, ContentFile(buf.getvalue()), save=False)
    # Sauvegarde silencieuse (évite boucle de signaux)
    Invite.objects.filter(pk=instance.pk).update(qr_code=instance.qr_code.name)


class InvitationTemplate(models.Model):
    """
    Template d'invitation généré par le Studio de Création (Builder No-code drag&drop).
    Un template est unique par événement (Event).
    """
    event = models.OneToOneField(
        Event, 
        on_delete=models.CASCADE, 
        related_name="invitation_template"
    )
    # Les différents contenus sauvegardés par le builder
    html_content = models.TextField(blank=True, default="")
    css_content = models.TextField(blank=True, default="")
    components_data = models.TextField(blank=True, default="[]", help_text="Données JSON structurelles (GrapesJS)")
    styles_data = models.TextField(blank=True, default="[]", help_text="Styles JSON (GrapesJS)")
    
    # Paramètres de l'animation Invité
    has_envelope_animation = models.BooleanField(default=True, help_text="Activer l'animation 3D de l'enveloppe à l'ouverture")
    music_url = models.URLField(blank=True, null=True, help_text="Lien vers une musique de fond (Optionnel)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Template d'Invitation pour : {self.event.name}"
