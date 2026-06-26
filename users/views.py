from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Membership
from movies.models import Review
from movies.views import get_user_plan

User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        
def terms_view(request):
    return render(request, 'users/terms.html')

@require_POST
def accept_terms(request):
    # Aceptar términos modifica estado (flag de sesión previo al registro), por
    # lo que debe ser POST exclusivamente. Un GET responde 405 automáticamente.
    # No lleva @login_required: se usa antes de que exista el usuario.
    request.session['accepted_terms'] = True
    return redirect('register')

def register_view(request):
    if not request.session.get('accepted_terms'):
        return redirect('terms')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            del request.session['accepted_terms']
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

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

@login_required(login_url='/users/login/')
def perfil_view(request):
    try:
        membership = Membership.objects.get(user=request.user)
    except Membership.DoesNotExist:
        membership = None
    reviews = Review.objects.filter(user=request.user).select_related('movie')
    return render(request, 'users/perfil.html', {
        'perfil_user': request.user,
        'membership': membership,
        'es_dueno': True,
        'reviews': reviews,
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
    reviews = Review.objects.filter(user=perfil_user).select_related('movie')
    return render(request, 'users/perfil.html', {
        'perfil_user': perfil_user,
        'membership': membership,
        'es_dueno': es_dueno,
        'reviews': reviews,
    })

@login_required(login_url='/users/login/')
def perfil_editar(request):
    plan = get_user_plan(request.user)

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