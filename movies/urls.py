from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:pk>/watchlist/', views.watchlist_toggle, name='watchlist_toggle'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
]