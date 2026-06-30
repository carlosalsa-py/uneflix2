from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError
from .models import Membership
from movies.models import Review
from movies.views import get_user_plan

User = get_user_model()

# Contrato del avatar: el cropper del frontend siempre exporta un JPEG de
# exactamente 128x128px. Estas constantes son el respaldo server-side por si
# alguien saltea el JS (request directo, DevTools). Las dimensiones se exigen
# exactas, no "hasta": cualquier tamaño distinto significa que el archivo no
# pasó por nuestro pipeline, así que se rechaza.
AVATAR_MAX_BYTES = 128 * 1024  # 128KB
AVATAR_SIZE = (128, 128)
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

        if avatar:
            # Validación de respaldo: el JS puede saltearse, así que nunca
            # confiamos en que el archivo ya venga recortado. Si algo no
            # cuadra, no guardamos nada y avisamos (patrón de pago()).
            if avatar.size > AVATAR_MAX_BYTES:
                messages.error(request, 'La foto de perfil supera los 128KB permitidos.')
                return redirect('perfil_editar')

            try:
                image = Image.open(avatar)
                image.verify()
            except (UnidentifiedImageError, OSError):
                messages.error(request, 'El archivo no es una imagen válida.')
                return redirect('perfil_editar')

            if image.size != AVATAR_SIZE:
                messages.error(request, 'La foto de perfil debe ser de exactamente 128x128 píxeles.')
                return redirect('perfil_editar')

            # verify() consume el archivo; lo rebobinamos para que Django
            # guarde el contenido completo y no un stream vacío.
            avatar.seek(0)
            request.user.avatar = avatar

        request.user.display_name = display_name
        request.user.save()
        return redirect('perfil')

    return render(request, 'users/perfil_editar.html')