# scanner/views.py
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from guests.models import Invitation

@login_required
def scan_page(request):
    """
    Page de scan "simple".
    - Si un ?token=... est présent dans l'URL, le JS de la page fera automatiquement l'appel à l'API.
    - Sinon, on peut coller le token manuellement puis valider.
    """
    return render(request, "scanner/scan.html")

@login_required
@require_POST
def scan_token(request):
    """
    API de scan.
    Attend un 'token' dans body (FormData ou x-www-form-urlencoded).
    Répond en JSON avec:
      ok, first_time, guest, event, table, first_scanned_at
    """
    token = request.POST.get('token')
    if not token:
        return JsonResponse({'ok': False, 'error': 'TOKEN_MISSING'}, status=400)

    try:
        inv = Invitation.objects.select_related(
            'guest', 'table', 'guest__event', 'guest__event__organization'
        ).get(qr_token=token)
    except Invitation.DoesNotExist:
        raise Http404("Invalid token")

    # Première validation ?
    first = False
    if inv.first_scanned_at is None:
        inv.first_scanned_at = timezone.now()
        inv.save(update_fields=['first_scanned_at'])
        first = True

    # Journaliser tous les scans
    inv.checkins.create(by_user=request.user)

    table_label = inv.table.label if inv.table else None
    return JsonResponse({
        'ok': True,
        'first_time': first,
        'guest': inv.guest.full_name,
        'event': inv.guest.event.name,
        'table': table_label,
        'first_scanned_at': inv.first_scanned_at.isoformat() if inv.first_scanned_at else None,
    })
