from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Recuperación de contraseña (vistas nativas de Django + plantillas propias
    # en templates/registration/). El email sale por EMAIL_BACKEND (consola en
    # dev, SMTP en prod).
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('terms/', views.terms_view, name='terms'), # Aquí definimos el nombre 'terms'
    path('terms/accept/', views.accept_terms, name='accept_terms'),
]
