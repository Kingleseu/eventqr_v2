from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

def mfa_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # En dev, on ne bloque pas (pratique pour avancer)
        if getattr(settings, "DEBUG", False):
            return view_func(request, *args, **kwargs)

        # En prod: si pas connecté, on laisse login_required gérer ailleurs
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # Ici, on devrait vérifier si l'utilisateur a bien configuré la MFA.
        # Pour rester simple (et sûr), si ce n'est pas le cas on redirige
        # vers la page de configuration MFA d'allauth.
        has_mfa = request.session.get("allauth_mfa_verified") or request.session.get("allauth_mfa_enrolled")
        if has_mfa:
            return view_func(request, *args, **kwargs)

        # Message + redirection vers la page MFA (et pas vers le dashboard,
        # ça évite d'empiler les messages sur le dashboard).
        if not request.session.get("mfa_warned_once"):
            messages.warning(request, "Active la MFA avant d'accéder à cette page.")
            request.session["mfa_warned_once"] = True
        return redirect("/accounts/mfa/")
    return wrapper
