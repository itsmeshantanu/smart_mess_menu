from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('owner-inquiry/', views.owner_inquiry, name='owner_inquiry'),
    path('owner-inquiry/success/', views.owner_inquiry_success, name='owner_inquiry_success'),

    # Mess listing & detail
    path('mess/', views.mess_list, name='mess_list'),
    path('mess/<int:pk>/', views.mess_detail, name='mess_detail'),

    # Nearby
    path('mess/nearby/', views.nearby_messes, name='nearby_messes'),

    # Rating & Favorites
    path('mess/<int:pk>/rate/', views.rate_mess, name='rate_mess'),
    path('mess/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.my_favorites, name='my_favorites'),

    # Owner management
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/mess/create/', views.create_mess, name='create_mess'),
    path('owner/mess/<int:pk>/edit/', views.edit_mess, name='edit_mess'),
    path('owner/mess/<int:pk>/photos/', views.manage_photos, name='manage_photos'),
    path('owner/photo/<int:photo_pk>/cover/', views.set_cover_photo, name='set_cover_photo'),
    path('owner/photo/<int:photo_pk>/delete/', views.delete_photo, name='delete_photo'),
    path('owner/mess/<int:mess_pk>/menu/create/', views.create_menu, name='create_menu'),
    path('owner/menu/<int:pk>/edit/', views.edit_menu, name='edit_menu'),
    path('owner/menu/<int:pk>/manage/', views.manage_menu, name='manage_menu'),
    path('owner/dish/<int:pk>/delete/', views.delete_dish, name='delete_dish'),
]
