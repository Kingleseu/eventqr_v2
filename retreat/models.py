# retreat/models.py
from __future__ import annotations

import base64
import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from events.models import Event

User = get_user_model()

# -- Util de chiffrement : on essaie d'importer, sinon fallback base64 --
try:
    from .utils import encrypt_qr_data  # optionnel
except Exception:  # pragma: no cover
    def encrypt_qr_data(s: str) -> str:
        # NOTE: ce n'est PAS un vrai chiffrement, juste un fallback léger.
        return base64.urlsafe_b64encode(s.encode()).decode()


# ===================== Paramétrage & journalisation =====================

class Parametrage(models.Model):
    inscription_active = models.BooleanField(default=True, verbose_name="Ouverture des inscriptions")
    maintenance_mode = models.BooleanField(default=False, verbose_name="Mode maintenance (bloque tout)")
    date_modif = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        state = "on" if self.inscription_active else "off"
        return f"Paramétrage (inscriptions={state})"


class Testimony(models.Model):
    name = models.CharField("Nom", max_length=64)
    message = models.TextField("Témoignage")

    COLOR_CHOICES = [
        ('rose', 'Rose'), ('bleu', 'Bleu'), ('jaune', 'Jaune'),
        ('vert', 'Vert'), ('violet', 'Violet'), ('gris', 'Gris'),
    ]
    color = models.CharField("Couleur", choices=COLOR_CHOICES, max_length=12, default='rose')
    date_submitted = models.DateTimeField(auto_now_add=True)
    validated = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.message[:40]}"


class LogAction(models.Model):
    ACTION_TYPES = [
        ('connexion', "Connexion"),
        ('access', "Accès page"),
        ('create', "Création"),
        ('update', "Modification"),
        ('delete', "Suppression"),
        ('param', "Paramétrage"),
        ('other', "Autre"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES, default='other')
    action = models.CharField(max_length=150)
    details = models.TextField(blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.date_action:%Y-%m-%d %H:%M} - {self.user} - {self.action}"


# =========================== Noyau Retraite ============================

class Responsable(models.Model):
    M, F = 'M', 'F'
    SEXE_CHOICES = [(M, 'M'), (F, 'F')]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    age = models.IntegerField(null=True, blank=True)
    # Lien souple vers un atelier précis (optionnel)
    atelier = models.ForeignKey(
        'Atelier', null=True, blank=True, on_delete=models.SET_NULL,
        related_name="responsables_directs"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='Responsable_owned', null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} ({self.sexe})"


class Chambre(models.Model):
    M, F = 'M', 'F'
    SEXE_CHOICES = [(M, 'M'), (F, 'F')]

    # Rattachement à l'événement (CRUCIAL)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='chambres')

    # Nom libre : "Chambre A", "A", "1", etc.
    nom = models.CharField(max_length=50)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, blank=True, null=True)
    capacite = models.PositiveIntegerField(default=10)

    responsables = models.ManyToManyField(Responsable, blank=True, related_name='chambres')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='chambres_owned', null=True, blank=True
    )

    class Meta:
        ordering = ['nom']
        constraints = [
            models.UniqueConstraint(fields=['event', 'nom', 'sexe'], name='uniq_chambre_event_nom_sexe'),
        ]
        indexes = [
            models.Index(fields=['event', 'sexe']),
        ]

    def __str__(self) -> str:
        return f"{self.nom} ({self.sexe or 'mixte'}) · {self.event.name}"


class Atelier(models.Model):
    # Rattachement à l'événement (CRUCIAL)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ateliers')

    numero = models.PositiveIntegerField()
    responsables = models.ManyToManyField(Responsable, blank=True, related_name='ateliers')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ateliers_owned', null=True, blank=True
    )

    class Meta:
        ordering = ['numero']
        constraints = [
            models.UniqueConstraint(fields=['event', 'numero'], name='uniq_atelier_event_numero'),
        ]
        indexes = [
            models.Index(fields=['event', 'numero']),
        ]

    def __str__(self) -> str:
        return f"Atelier {self.numero} · {self.event.name}"


class Participant(models.Model):
    # Rattachement à l'événement (CRUCIAL)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')

    PARTICIPANT = 'Participant'
    OUVRIER = 'ouvrier'
    ROLE_CHOICES = [
        (PARTICIPANT, 'Participant'),
        (OUVRIER, 'Ouvrier de la jeunesse'),
    ]
    role_participant = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=PARTICIPANT, verbose_name="Type de participant"
    )

    M, F = 'M', 'F'
    SEXE_CHOICES = [(M, 'M'), (F, 'F')]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to='participants/photos/', blank=True, null=True)

    telephone = models.CharField(max_length=20, blank=True, null=True)
    telephone_urgence = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)

    present = models.BooleanField(default=False)
    date_presence = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='participants_owned', null=True, blank=True
    )

    billet_envoye = models.BooleanField(default=False)
    billet_envoye_email = models.BooleanField(default=False)
    billet_envoye_whatsapp = models.BooleanField(default=False)
    billet_pdf = models.FileField(upload_to='billets/', blank=True, null=True)
    date_billet_envoye = models.DateTimeField(null=True, blank=True)
    download_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)

    preuve_paiement = models.FileField(upload_to='preuves_paiement/', blank=True, null=True)
    paiement_valide = models.BooleanField(default=False)
    observation = models.TextField(blank=True, null=True)

    chambre = models.ForeignKey(Chambre, on_delete=models.SET_NULL, null=True, blank=True)
    atelier = models.ForeignKey(Atelier, on_delete=models.SET_NULL, null=True, blank=True)

    qr_code = models.ImageField(
        upload_to='qr_codes/', blank=True, null=True,
        help_text="QR code reprenant nom, prénom, chambre et atelier"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'nom', 'prenom'], name='uniq_participant_event_nom_prenom'),
        ]
        permissions = [
            ("acces_billets", "Accès à la gestion des billets"),
            ("acces_paiements", "Accès à la gestion des paiements"),
            ("acces_groupes", "Accès à la gestion des groupes et ateliers"),
            ("acces_scan", "Accès au scan QR code"),
            ("acces_participants", "Accès à la gestion des participants"),
            ("acces_presence", "Accès à la liste des présences"),
            ("acces_parametrage", "Accès au paramétrage"),
        ]
        indexes = [
            models.Index(fields=['event', 'nom', 'prenom']),
        ]

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} · {self.event.name}"

    # ---------- Cohérence ----------
    def clean(self):
        errors = {}
        if self.chambre and self.chambre.event_id != self.event_id:
            errors['chambre'] = "La chambre sélectionnée appartient à un autre événement."
        if self.atelier and self.atelier.event_id != self.event_id:
            errors['atelier'] = "L’atelier sélectionné appartient à un autre événement."
        if errors:
            raise ValidationError(errors)

    @property
    def has_whatsapp(self) -> bool:
        return bool(self.telephone and self.telephone.startswith('+'))

    # ---------- Données QR ----------
    def get_qr_plain_data(self) -> str:
        chambre_nom = self.chambre.nom if self.chambre else "Non attribuée"
        atelier_num = self.atelier.numero if self.atelier else "Non attribué"
        return (
            f"{self.nom} {self.prenom} | Âge: {self.age} | Sexe: {self.sexe or '-'} | "
            f"Chambre: {chambre_nom} | Atelier: {atelier_num} | Event: {self.event.name}"
        )

    def get_qr_data(self) -> str:
        return encrypt_qr_data(self.get_qr_plain_data())

    def save(self, *args, **kwargs):
        # Valide la cohérence avant de générer le QR
        self.full_clean(exclude=['qr_code'])

        data = self.get_qr_data()
        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10, border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f"qr_{self.nom.lower()}_{self.prenom.lower()}.png"
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)


# ========================= OTP / Billets / Notifs ======================

class OTPVerification(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=(('email', 'Email'), ('sms', 'SMS')), default='email')


class BilletGlobalFiles(models.Model):
    reglement_pdf = models.FileField(upload_to="billets_globaux/", blank=True, null=True)
    objets_pdf = models.FileField(upload_to="billets_globaux/", blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=256)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self) -> str:
        who = self.user or 'Admin'
        return f"Notif to {who} : {self.message[:30]}"
