# events/urls.py
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('new/', views.EventCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.EventUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='delete'),
    path('<int:pk>/toggle-active/', views.EventToggleActiveView.as_view(), name='toggle_active'),

    # Tables
    path('<int:event_pk>/tables/new/', views.TableCreateView.as_view(), name='table_create'),
    path('<int:event_pk>/tables/bulk/', views.BulkTablesCreateView.as_view(), name='table_bulk'),
    path('<int:event_pk>/tables/<int:table_pk>/edit/', views.TableUpdateView.as_view(), name='table_edit'),
    path('<int:event_pk>/tables/<int:table_pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),

    # Retreat
    path('<int:pk>/retreat/', views.RetreatEditView.as_view(), name='retreat_edit'),
]
