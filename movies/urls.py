from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:pk>/watchlist/', views.watchlist_toggle, name='watchlist_toggle'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('movie/<int:pk>/play/', views.player_view, name='player'),
    path('episode/<int:pk>/play/', views.episode_player, name='episode_player'),
    
    # Rutas para las membresías y la página de pago
    path('membresias/', views.membresias, name='membresias'),
    path('pago/', views.pago, name='pago'),
    
    path('anuncio/<int:num>/', views.anuncio, name='anuncio'),
    path('movie/<int:pk>/review/', views.review_submit, name='review_submit'),
    path('review/<int:pk>/delete/', views.review_delete, name='review_delete'),
]