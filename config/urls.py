from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (allauth) — adapte si besoin
    path('accounts/', include('allauth.urls')),

    # Hub (dashboard général)
    path('dashboard/', include(('dash.urls', 'dashboard'), namespace='dashboard')),

    # Apps
    path('guests/', include(('guests.urls', 'guests'), namespace='guests')),
    path('retreat/', include(('retreat.urls', 'retreat'), namespace='retreat')),

    # Page racine -> redirige vers dashboard
    path('', include(('dash.urls', 'dashboard'), namespace='dashboard-root')),
]
