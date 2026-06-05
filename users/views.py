from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Membership

User = get_user_model()

# --- VISTAS DE TÉRMINOS Y REGISTRO ---

def terms_view(request):
    return render(request, 'users/terms.html')

def accept_terms(request):
    request.session['accepted_terms'] = True
    return redirect('register')

def register_view(request):
    # Seguridad: Si no aceptó términos, redirigir a términos
    if not request.session.get('accepted_terms'):
        return redirect('terms')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST) # O tu CustomUserCreationForm
        if form.is_valid():
            form.save()
            # Limpiamos la sesión tras el registro exitoso
            del request.session['accepted_terms']
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# --- VISTAS DE AUTENTICACIÓN ---

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- VISTAS DE PERFIL ---

@login_required(login_url='/users/login/')
def perfil_view(request):
    try:
        membership = Membership.objects.get(user=request.user)
    except Membership.DoesNotExist:
        membership = None
    return render(request, 'users/perfil.html', {
        'perfil_user': request.user,
        'membership': membership,
        'es_dueno': True,
    })

def perfil_publico(request, username):
    perfil_user = get_object_or_404(User, username=username)
    es_dueno = request.user.is_authenticated and request.user.username == username
    membership = None
    if es_dueno:
        try:
            membership = Membership.objects.get(user=perfil_user)
        except Membership.DoesNotExist:
            pass
    return render(request, 'users/perfil.html', {
        'perfil_user': perfil_user,
        'membership': membership,
        'es_dueno': es_dueno,
    })

@login_required(login_url='/users/login/')
def perfil_editar(request):
    try:
        membership = Membership.objects.get(user=request.user)
        plan = membership.plan if membership.status == 'active' else 'free'
    except Membership.DoesNotExist:
        plan = 'free'

    if plan == 'free':
        return redirect('membresias')

    if request.method == 'POST':
        display_name = request.POST.get('display_name', '')
        avatar = request.FILES.get('avatar')
        request.user.display_name = display_name
        if avatar:
            request.user.avatar = avatar
        request.user.save()
        return redirect('perfil')

    return render(request, 'users/perfil_editar.html')