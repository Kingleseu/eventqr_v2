from django.urls import path
from . import views

app_name = 'retreat'

urlpatterns = [
    path('', views.home, name='home'),  
    path("event/<int:pk>/",views.event_detail,name="event_detail"),
]
