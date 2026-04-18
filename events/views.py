# events/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View

from core.mixins import OrganizationQuerysetMixin
from .models import Event, Table, EventType
from .forms import EventForm, TableForm, BulkTablesForm, RetreatInfoForm

class EventListView(LoginRequiredMixin, OrganizationQuerysetMixin, ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        typ = self.request.GET.get('type')
        if q:
            qs = qs.filter(name__icontains=q)
        if typ:
            qs = qs.filter(event_type=typ)
        return qs.order_by('-starts_at', 'name')

class EventDetailView(LoginRequiredMixin, OrganizationQuerysetMixin, DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        event = self.object
        ctx['tables'] = Table.objects.filter(event=event).order_by('label')
        # Statistiques simples (invités) si tu veux plus tard: counts par table, etc.
        # ctx['guests_count'] = event.guest_set.count()
        return ctx

class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def get_initial(self):
        initial = super().get_initial()
        profile = getattr(self.request.user, 'userprofile', None)
        if profile:
            initial['organization'] = profile.organization
        return initial

    def form_valid(self, form):
        # verrouille l’organisation à celle du user si tu veux éviter de changer
        profile = getattr(self.request.user, 'userprofile', None)
        if profile:
            form.instance.organization = profile.organization
        messages.success(self.request, "Événement créé.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('events:detail', args=[self.object.pk])

class EventUpdateView(LoginRequiredMixin, OrganizationQuerysetMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Événement mis à jour.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('events:detail', args=[self.object.pk])

class EventDeleteView(LoginRequiredMixin, OrganizationQuerysetMixin, DeleteView):
    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy('events:list')

# --- Tables ---

class TableCreateView(LoginRequiredMixin, View):
    template_name = "events/table_form.html"

    def get(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = TableForm()
        return render(request, self.template_name, {'event': event, 'form': form})

    def post(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = TableForm(request.POST)
        if form.is_valid():
            tbl = form.save(commit=False)
            tbl.event = event
            tbl.save()
            messages.success(request, "Table ajoutée.")
            return redirect('events:detail', pk=event.pk)
        return render(request, self.template_name, {'event': event, 'form': form})

class TableUpdateView(LoginRequiredMixin, View):
    template_name = "events/table_form.html"

    def get(self, request, event_pk, table_pk):
        event = get_object_or_404(Event, pk=event_pk)
        table = get_object_or_404(Table, pk=table_pk, event=event)
        form = TableForm(instance=table)
        return render(request, self.template_name, {'event': event, 'form': form, 'table': table})

    def post(self, request, event_pk, table_pk):
        event = get_object_or_404(Event, pk=event_pk)
        table = get_object_or_404(Table, pk=table_pk, event=event)
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, "Table modifiée.")
            return redirect('events:detail', pk=event.pk)
        return render(request, self.template_name, {'event': event, 'form': form, 'table': table})

class TableDeleteView(LoginRequiredMixin, View):
    template_name = "events/table_confirm_delete.html"

    def get(self, request, event_pk, table_pk):
        event = get_object_or_404(Event, pk=event_pk)
        table = get_object_or_404(Table, pk=table_pk, event=event)
        return render(request, self.template_name, {'event': event, 'table': table})

    def post(self, request, event_pk, table_pk):
        event = get_object_or_404(Event, pk=event_pk)
        table = get_object_or_404(Table, pk=table_pk, event=event)
        table.delete()
        messages.success(request, "Table supprimée.")
        return redirect('events:detail', pk=event.pk)

class BulkTablesCreateView(LoginRequiredMixin, View):
    template_name = "events/table_bulk_form.html"

    def get(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = BulkTablesForm(initial={'base_label': 'Table', 'count': 10, 'capacity': 10})
        return render(request, self.template_name, {'event': event, 'form': form})

    def post(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = BulkTablesForm(request.POST)
        if form.is_valid():
            base = form.cleaned_data['base_label']
            count = form.cleaned_data['count']
            capacity = form.cleaned_data['capacity']
            created = 0
            for i in range(1, count + 1):
                label = f"{base} {i}"
                # évite doublons (unique_together event+label)
                Table.objects.get_or_create(event=event, label=label, defaults={'capacity': capacity})
                created += 1
            messages.success(request, f"{created} tables générées (les doublons éventuels ont été ignorés).")
            return redirect('events:detail', pk=event.pk)
        return render(request, self.template_name, {'event': event, 'form': form})

# --- Activer/Désactiver un événement ---

class EventToggleActiveView(LoginRequiredMixin, OrganizationQuerysetMixin, View):
    def post(self, request, pk):
        ev = get_object_or_404(Event, pk=pk)
        ev.is_active = not ev.is_active
        ev.save(update_fields=['is_active'])
        messages.info(request, f"Événement {'activé' if ev.is_active else 'désactivé'}.")
        return redirect('events:detail', pk=ev.pk)
    
# --- RetreatInfo : édition conditionnelle ---

class RetreatEditView(LoginRequiredMixin, OrganizationQuerysetMixin, View):
    template_name = "events/retreat_form.html"

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if event.event_type != EventType.RETREAT:
            messages.warning(request, "Cet événement n'est pas de type 'Retraite'.")
            return redirect('events:detail', pk=event.pk)
        retreat = getattr(event, 'retreat', None)
        form = RetreatInfoForm(instance=retreat)
        return render(request, self.template_name, {'event': event, 'form': form})

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if event.event_type != EventType.RETREAT:
            messages.warning(request, "Cet événement n'est pas de type 'Retraite'.")
            return redirect('events:detail', pk=event.pk)
        retreat = getattr(event, 'retreat', None)
        form = RetreatInfoForm(request.POST, instance=retreat)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.event = event
            obj.save()
            messages.success(request, "Informations 'Retraite' enregistrées.")
            return redirect('events:detail', pk=event.pk)
        return render(request, self.template_name, {'event': event, 'form': form})
