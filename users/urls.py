from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('terms/', views.terms_view, name='terms'), # Aquí definimos el nombre 'terms'
    path('terms/accept/', views.accept_terms, name='accept_terms'),
]
