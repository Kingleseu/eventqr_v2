# guests/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Invite, Table


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invite
        fields = ["nom", "prenom", "tele", "table"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "tele": forms.TextInput(attrs={"class": "form-control"}),
            "table": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)
        self.event = event
        if event:
            self.fields["table"].queryset = Table.objects.filter(event=event).order_by("numero")
        else:
            self.fields["table"].queryset = Table.objects.none()

    def clean(self):
        cleaned = super().clean()
        nom = cleaned.get("nom") or ""
        prenom = cleaned.get("prenom") or ""
        tele = cleaned.get("tele") or ""
        
        # Si champs obligatoires manquants, on laisse faire (géré par required=True)
        if not nom or not prenom:
            return cleaned

        qs = Invite.objects.all()
        if self.event:
            qs = qs.filter(event=self.event)
        
        # Exclure l'invité en cours d'édition (si update)
        if getattr(self, "instance", None) and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        # 1. Vérification Nom + Prénom (Exact ou Inversé)
        # On vérifie "Nom + Prénom" ET "Prénom + Nom" pour éviter les doublons inversés
        name_dup = qs.filter(
            Q(nom__iexact=nom, prenom__iexact=prenom) | 
            Q(nom__iexact=prenom, prenom__iexact=nom)
        ).exists()
        
        if name_dup:
            raise ValidationError(f"Un invité nommé '{prenom} {nom}' existe déjà dans cet événement.")

        # 2. Vérification Téléphone: SUPPRIMÉE SUR DEMANDE UTILISATEUR
        # Plusieurs invités peuvent avoir le même numéro (couples, familles)
        # if tele:
        #     tele_dup = qs.filter(tele__iexact=tele).exists()
        #     if tele_dup:
        #         raise ValidationError(f"Le numéro de téléphone '{tele}' est déjà utilisé par un autre invité.")

        return cleaned


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
    class Meta:
        model = Table
        fields = ["numero", "nom", "color", "shape", "nombre_de_places"]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control", "placeholder": "1, 2, A..."}),
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Table d'Honneur"}),
            "color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color", "title": "Choisir une couleur"}),
            "shape": forms.Select(attrs={"class": "form-select"}),
            "nombre_de_places": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }


class AddInviteToTableForm(forms.Form):
    invite = forms.ModelChoiceField(
        queryset=Invite.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    table = forms.ModelChoiceField(
        queryset=Table.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields["invite"].queryset = Invite.objects.filter(event=event).order_by("nom", "prenom")
            # --- CUSTOMIZATION: Afficher seulement "Nom Prénom" sans l'événement ---
            self.fields["invite"].label_from_instance = lambda obj: f"{obj.nom} {obj.prenom}"
            
            self.fields["table"].queryset = Table.objects.filter(event=event).order_by("numero")
        else:
            self.fields["invite"].queryset = Invite.objects.none()
            self.fields["table"].queryset = Table.objects.none()
