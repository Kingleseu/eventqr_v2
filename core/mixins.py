from django.contrib.auth.mixins import LoginRequiredMixin


class OrganizationQuerysetMixin(LoginRequiredMixin):
    """Filtre automatiquement les QuerySets par l'organisation du user si le modèle a un champ 'organization'."""
    def get_queryset(self):
        qs = super().get_queryset()
        profile = getattr(self.request.user, 'userprofile', None)
        if profile and hasattr(qs.model, 'organization'):
            return qs.filter(organization=profile.organization)
        return qs