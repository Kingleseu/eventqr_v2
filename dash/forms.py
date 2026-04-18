# dash/forms.py
from django import forms
from events.models import Event

class EventQuickForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['organization', 'name', 'event_type', 'starts_at', 'ends_at', 'venue']
        labels = {
            'organization': "Organisation",
            'name': "Nom de l'événement",
            'event_type': "Type d'événement",
            'starts_at': "Début",
            'ends_at': "Fin",
            'venue': "Lieu",
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        kind = kwargs.pop('kind', None)
        super().__init__(*args, **kwargs)
        # Optionnel : présélectionne le type selon ?kind=guests|retreat
        if kind in ('guests', 'retreat') and not self.is_bound:
            self.fields['event_type'].initial = kind
        self.fields['organization'].widget.attrs.update({'class': 'form-select'})
        self.fields['event_type'].widget.attrs.update({'class': 'form-select'})


class QuickGuestsForm(forms.Form):
    base_label = forms.CharField(initial='Table', label="Préfixe", widget=forms.TextInput(attrs={'class': 'form-control'}))
    count = forms.IntegerField(min_value=0, initial=10, label="Nombre de tables", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    capacity = forms.IntegerField(min_value=1, initial=10, label="Capacité par table", widget=forms.NumberInput(attrs={'class': 'form-control'}))


class QuickRetreatForm(forms.Form):
    rooms_male = forms.IntegerField(min_value=0, initial=6, label="Chambres (Hommes)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    rooms_female = forms.IntegerField(min_value=0, initial=6, label="Chambres (Femmes)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    room_capacity = forms.IntegerField(min_value=1, initial=10, label="Capacité par chambre", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    ateliers_count = forms.IntegerField(min_value=0, initial=6, label="Nombre d'ateliers", widget=forms.NumberInput(attrs={'class': 'form-control'}))
