from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from events.models import Event

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from events.models import Event

@login_required
def home(request):
    event_id = request.GET.get("event")
    active_event = None
    if event_id:
        active_event = get_object_or_404(Event, pk=event_id, event_type="retreat")
        request.session["active_event_id"] = active_event.pk
    return render(request, "retreat/home.html", {"active_event": active_event})

@login_required
def event_detail(request, pk: int):
    ev = get_object_or_404(Event, pk=pk)
    # related_name = 'chambres' / 'ateliers'
    chambres = ev.chambres.all() if hasattr(ev, "chambres") else []
    ateliers = ev.ateliers.all() if hasattr(ev, "ateliers") else []
    return render(request, "retreat/event_detail.html",
                  {"event": ev, "chambres": chambres, "ateliers": ateliers})
