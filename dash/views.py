# config/dash/views.py
from __future__ import annotations

from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from events.models import Event, EventType
from guests.models import Invite, Table, InvitationStatus

# ---------------------------------------------------------
# Organization (facultatif) : on importe si présent
# ---------------------------------------------------------
try:
    from core.models import Organization
except Exception:
    Organization = None


# ---------------------------------------------------------
# Helpers Organization (facultatif)
# ---------------------------------------------------------
def _unique_slug(base: str) -> str:
    """
    Retourne un slug unique pour Organization en ajoutant -2, -3, ...
    """
    base = base or "org"
    candidate = base
    n = 2
    while Organization and Organization.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def _attach_user_to_org(user, org):
    """
    Lie l'utilisateur à l'organisation selon le modèle dispo.
    """
    if not org:
        return
    if hasattr(org, "members"):
        org.members.add(user)
    elif hasattr(org, "users"):
        org.users.add(user)
    elif hasattr(org, "owner_id") and org.owner_id is None:
        org.owner = user
        org.save(update_fields=["owner"])


def _ensure_user_org(user):
    """
    1) Si l'utilisateur est déjà rattaché à une org → renvoie-la.
    2) Sinon cherche une org dont il est owner.
    3) Sinon crée une org avec slug unique basé sur l'utilisateur.
    """
    if not Organization:
        return None

    # 1) déjà membre ?
    try:
        m = getattr(user, "organization_set", None) or getattr(user, "organizations", None)
        if m:
            org = m.first()
            if org:
                return org
    except Exception:
        pass

    # 2) déjà owner ?
    try:
        if hasattr(Organization, "owner"):
            org = Organization.objects.filter(owner=user).first()
            if org:
                return org
    except Exception:
        pass

    # 3) créer si besoin
    base_slug = slugify(
        (getattr(user, "username", "") or getattr(user, "email", "").split("@")[0] or "org")
    )
    name = f"Organisation de {(getattr(user, 'get_full_name', lambda: '')() or getattr(user, 'username', '') or 'Utilisateur')}".strip()

    org = Organization.objects.filter(slug=base_slug).first()
    if org:
        _attach_user_to_org(user, org)
        return org

    with transaction.atomic():
        slug = _unique_slug(base_slug)
        fields = {"name": name, "slug": slug}
        if hasattr(Organization, "owner"):
            fields["owner"] = user
        org = Organization.objects.create(**fields)
        _attach_user_to_org(user, org)
        return org


# ---------------------------------------------------------
# Forms (si tu veux des formulaires rapides sur le dashboard)
# ---------------------------------------------------------
_DT_FORMAT = "%Y-%m-%dT%H:%M"  # format pour <input type="datetime-local">


class EventQuickForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "starts_at", "ends_at", "venue"]  # le type est fixé côté vue
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex : Gala 2025 / Retraite de jeunesse"
            }),
            "starts_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format=_DT_FORMAT,
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format=_DT_FORMAT,
            ),
            "venue": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Lieu (facultatif)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = [_DT_FORMAT]
        self.fields["ends_at"].input_formats = [_DT_FORMAT]


class QuickTablesForm(forms.Form):
    base_label = forms.CharField(
        initial="Table", label="Préfixe",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    count = forms.IntegerField(
        min_value=0, initial=10, label="Nombre de tables",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    capacity = forms.IntegerField(
        min_value=1, initial=10, label="Capacité par table",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )


class RetreatBootstrapForm(forms.Form):
    rooms_male = forms.IntegerField(
        min_value=0, initial=7, label="Chambres Hommes",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    rooms_female = forms.IntegerField(
        min_value=0, initial=7, label="Chambres Femmes",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    room_capacity = forms.IntegerField(
        min_value=1, initial=10, label="Capacité par chambre",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    ateliers_count = forms.IntegerField(
        min_value=0, initial=5, label="Nombre d’ateliers",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )


# ---------------------------------------------------------
# Utils
# ---------------------------------------------------------
def _parse_local_dt(dt_str: str):
    """
    Parse une chaîne 'YYYY-MM-DDTHH:MM' depuis <input type="datetime-local">
    et la rend timezone-aware si USE_TZ = True.
    """
    if not dt_str:
        return None
    dt = parse_datetime(dt_str)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


# ---------------------------------------------------------
# Vues Dashboard
# ---------------------------------------------------------
@login_required
def index(request):
    """
    Dashboard : liste des derniers événements + stats agrégées
    """
    events = Event.objects.order_by("-starts_at")[:9]

    stats = {
        "events_total": Event.objects.count(),
        "invites_total": Invite.objects.count(),
        "invites_present": Invite.objects.filter(present=True).count(),
        "invites_confirmed": Invite.objects.filter(status=InvitationStatus.CONFIRMED).count(),
        "tables_total": Table.objects.count(),
    }
    return render(request, "dash/index.html", {"events": events, "stats": stats})


class EventCreateForm(forms.Form):
    event_type = forms.ChoiceField(
        choices=EventType.choices,
        label="Type d'événement",
        widget=forms.RadioSelect
    )
    name = forms.CharField(
        max_length=150,
        label="Nom de l'événement",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex : Mariage Sarah & Paul"})
    )
    venue = forms.CharField(
        required=False,
        max_length=200,
        label="Lieu",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex : Kinshasa, Salle XYZ"})
    )
    location_url = forms.URLField(
        required=False,
        label="Lien de localisation (Maps)",
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://maps..."}),
    )
    theme = forms.CharField(
        required=False,
        max_length=150,
        label="Thème",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex : Classy Gold / Retraite de prière"}),
    )
    starts_at = forms.DateTimeField(
        required=False,
        label="Date/heure début",
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        input_formats=[_DT_FORMAT],
    )
    ends_at = forms.DateTimeField(
        required=False,
        label="Date/heure fin",
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        input_formats=[_DT_FORMAT],
    )

    def clean(self):
        data = super().clean()
        starts = data.get("starts_at")
        ends = data.get("ends_at")
        if starts and ends and ends <= starts:
            self.add_error("ends_at", "La fin doit être après le début.")
        return data


@login_required
def event_new_guests(request):
    """
    Formulaire multi-step (front) pour créer un événement (invite ou retraite).
    GET : affiche le formulaire.
    POST : crée l'événement en base puis redirige vers le dashboard.
    """
    initial_type = request.GET.get("type") or EventType.INVITE
    initial_dt = timezone.now()
    initial = {
        "name": "",
        "event_type": initial_type,
        "starts_at": initial_dt.strftime(_DT_FORMAT),
        "ends_at": (initial_dt + timedelta(hours=2)).strftime(_DT_FORMAT),
        "venue": "",
        "theme": "",
        "location_url": "",
    }

    if request.method == "POST":
        form = EventCreateForm(request.POST)
        if form.is_valid():
            org = _ensure_user_org(request.user)
            starts_at = form.cleaned_data.get("starts_at") or timezone.now()
            ends_at = form.cleaned_data.get("ends_at") or (starts_at + timedelta(hours=2))
            ev = Event.objects.create(
                organization=org,
                name=form.cleaned_data["name"],
                event_type=form.cleaned_data["event_type"],
                starts_at=starts_at,
                ends_at=ends_at,
                venue=form.cleaned_data.get("venue") or "",
                theme=form.cleaned_data.get("theme") or "",
                location_url=form.cleaned_data.get("location_url") or "",
            )
            messages.success(request, f"Événement « {ev.name} » créé.")
            return redirect("dashboard:index")
    else:
        form = EventCreateForm(initial=initial)

    events = Event.objects.order_by("-starts_at")[:6]
    return render(request, "dash/event_new.html", {"form": form, "events": events})


@login_required
def event_new_retreat(request):
    """
    Redirige vers le formulaire unique en pré-sélectionnant RETREAT.
    """
    url = f"{reverse('dashboard:event_new_guests')}?type={EventType.RETREAT}"
    return redirect(url)


@require_POST
@login_required
def event_update(request, pk: int):
    """
    Cible du formulaire de la modale d’édition (méthode POST).
    Met à jour name/starts_at/ends_at/venue puis redirige vers le dashboard.
    """
    ev = get_object_or_404(Event, pk=pk)

    name = (request.POST.get("name") or "").strip()
    starts_at = _parse_local_dt(request.POST.get("starts_at"))
    ends_at = _parse_local_dt(request.POST.get("ends_at"))
    venue = (request.POST.get("venue") or "").strip() or None

    if name:
        ev.name = name
    if starts_at:
        ev.starts_at = starts_at
    if ends_at:
        ev.ends_at = ends_at
    ev.venue = venue
    ev.save()

    messages.success(request, f"Événement « {ev.name} » mis à jour.")
    return redirect("dashboard:index")


@require_POST
@login_required
def event_delete(request, pk: int):
    """
    Suppression d’un événement (form POST du dashboard).
    """
    ev = get_object_or_404(Event, pk=pk)
    name = ev.name
    ev.delete()
    messages.success(request, f"Événement « {name} » supprimé.")
    return redirect("dashboard:index")
