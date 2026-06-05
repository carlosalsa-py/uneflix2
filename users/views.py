from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Membership
from django.contrib.auth.decorators import login_required

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

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

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/users/login/')
def perfil_view(request):
    try:
        membership = Membership.objects.get(user=request.user)
    except Membership.DoesNotExist:
        membership = None
    return render(request, 'users/perfil.html', {
        'membership': membership,
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