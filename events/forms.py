# events/forms.py
from django import forms
from .models import Event, Table
from .models import RetreatInfo  # si tu as ajouté le modèle RetreatInfo

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['organization', 'name', 'event_type', 'starts_at', 'ends_at', 'venue', 'is_active']

class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['label', 'capacity']

class BulkTablesForm(forms.Form):
    base_label = forms.CharField(label="Préfixe", initial='Table')
    count = forms.IntegerField(label="Nombre de tables", min_value=1, initial=10)
    capacity = forms.IntegerField(label="Capacité", min_value=1, initial=10)

class RetreatInfoForm(forms.ModelForm):
    class Meta:
        model = RetreatInfo
        fields = ['coordinator_name', 'contact_phone', 'registration_fee', 'notes']
