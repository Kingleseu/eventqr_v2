# guests/urls.py
from django.urls import path
from . import views

app_name = "guests"

urlpatterns = [
    # Accueil
    path("", views.home, name="home"),

    # Invités
    path("invites/", views.add_invite, name="add_invite"),
    path("invites/bulk/", views.bulk_action, name="bulk_action"),
    path("invites/<int:pk>/edit/", views.update_invite, name="update_invite"),
    path("invites/<int:pk>/delete/", views.delete_invite, name="delete_invite"),
    path("invites/export/", views.export_invites, name="export_invites"),
    path("invites/template/", views.download_invites_template, name="download_invites_template"),
    path("search/", views.search_invites, name="search_invites"),

    # Tables management
    path("admin/", views.admin_page, name="admin"),
    path("tables/move-guest/", views.move_guest, name="move_guest"),
    path("tables/<int:table_id>/delete/", views.delete_table, name="delete_table"),
    path("tables/<int:table_id>/edit/", views.edit_table, name="edit_table"),

    # Invitations & présences
    path("invitations/", views.envoyer_invitations, name="envoyer_invitations"),
    path("presences/", views.liste_presences, name="liste_presences"),
    path("presences/export.csv", views.export_presences_csv, name="export_presences_csv"),

    # Scan
    path("scan/valider/", views.valider_qr_code, name="valider_qr_code"),
    
    # Table Plan
    path("tables/plan/", views.table_plan, name="table_plan"),
    path("tables/plan/save/", views.save_table_positions, name="save_table_positions"),

    # Studio Builder No-Code
    path("event/<int:event_id>/builder/", views.invitation_studio, name="invitation_studio"),
    path("api/builder/save/<int:event_id>/", views.save_template, name="save_template"),
    
    # Vue Publique de l'Invitation (Mini-site invité)
    path("i/<str:code>/", views.guest_invitation_view, name="guest_invitation"),
]
