# scanner/urls.py
from django.urls import path
from .views import scan_page, scan_token

urlpatterns = [
    path('scan/', scan_page, name='scan_page'),
    path('api/scan/', scan_token, name='scan_token'),
]
