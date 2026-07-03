import logging
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, F
from django.http import Http404
from django.utils import timezone
from .models import Movie, Genre, Watchlist, Episode, Review
from users.models import Membership

logger = logging.getLogger(__name__)

TIER_LEVEL = {'free': 0, 'medium': 1, 'premium': 2}

# Ordenamientos válidos del catálogo. 'rating' se maneja aparte porque necesita
# annotate(). El default (sin query param o valor desconocido) es '-id'.
CATALOGO_ORDEN = {
    'titulo_asc': 'title',
    'titulo_desc': '-title',
    'anio_nuevo': '-year',
    'anio_viejo': 'year',
}

# Fuente única de verdad de los planes pagos: el nombre visible y el precio se
# derivan SIEMPRE del código de plan en el backend, nunca de lo que mande el
# cliente. La clave es el código real del modelo Membership.
PLANES = {
    'medium': {'nombre': 'Cinéfilo', 'precio': '2.99'},
    'premium': {'nombre': 'Zerpanito', 'precio': '4.99'},
}

# Tiers que pueden dejar reseñas (Cinéfilo y Zerpanito). Los Unefista (free) no.
TIERS_CON_REVIEWS = ('medium', 'premium')

# Captura el ID (11 chars) de un video de YouTube en cualquier formato usual:
# watch?v=, youtu.be, /shorts/, /embed/, /v/, subdominios (m., music.,
# youtube-nocookie) e incluso pegado dentro del <iframe> de "Insertar".
_YOUTUBE_ID_RE = re.compile(
    r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|v/))'
    r'([\w-]{11})'
)


def extract_youtube_id(value):
    """Devuelve el ID de YouTube (11 chars) a partir de una URL, del código
    <iframe> de 'Insertar' o de un ID pelado. None si no se reconoce —así el
    template puede ocultar el trailer sin romper la página (vs. embed_video,
    que lanza excepción y tira 500 ante una URL que no reconoce)."""
    if not value:
        return None
    value = value.strip()
    match = _YOUTUBE_ID_RE.search(value)
    if match:
        return match.group(1)
    if re.fullmatch(r'[\w-]{11}', value):
        return value
    return None

def get_user_plan(user):
    try:
        membership = Membership.objects.get(user=user)
        return membership.plan if membership.status == 'active' else 'free'
    except Membership.DoesNotExist:
        return 'free'

@login_required(login_url='/users/login/')
def home(request):
    plan = get_user_plan(request.user)
    movies = Movie.objects.filter(type='movie')
    series = Movie.objects.filter(type='series')
    genres = Genre.objects.all()
    featured_movies = Movie.objects.filter(featured=True)

    # Sidebar (#10). Cada lista puede venir vacía (sin visitas, sin reseñas o sin
    # estrenos futuros cargados) y el template muestra un empty-state.
    mas_vistas = Movie.objects.filter(views__gt=0).order_by('-views')[:5]
    mejor_rateadas = (
        Movie.objects
        .annotate(avg_rating=Avg('reviews__rating'))
        .filter(avg_rating__isnull=False)
        .order_by('-avg_rating')[:5]
    )
    proximos_estrenos = (
        Movie.objects
        .filter(release_date__gt=timezone.localdate())
        .order_by('release_date')[:5]
    )

    return render(request, 'movies/home.html', {
        'movies': movies,
        'series': series,
        'genres': genres,
        'featured_movies': featured_movies,
        'plan': plan,
        'mas_vistas': mas_vistas,
        'mejor_rateadas': mejor_rateadas,
        'proximos_estrenos': proximos_estrenos,
    })

@login_required(login_url='/users/login/')
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)

    # Cuenta la visita sin traer una race condition (UPDATE atómico en la BD).
    # refresh_from_db para que el valor mostrado en esta misma request ya incluya
    # el +1 (si no, seguiría con el valor viejo cacheado en el objeto).
    Movie.objects.filter(pk=movie.pk).update(views=F('views') + 1)
    movie.refresh_from_db(fields=['views'])

    in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    seasons = movie.seasons.prefetch_related('episodes').all() if movie.type == 'series' else None

    plan = get_user_plan(request.user)
    can_watch = TIER_LEVEL.get(plan, 0) >= TIER_LEVEL.get(movie.tier, 0)
    can_review = TIER_LEVEL.get(plan, 0) >= TIER_LEVEL['medium']

    reviews = movie.reviews.select_related('user').all()
    user_review = reviews.filter(user=request.user).first()

    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    if avg_rating:
        avg_rating = round(avg_rating, 1)

    return render(request, 'movies/detail.html', {
        'movie': movie,
        'in_watchlist': in_watchlist,
        'seasons': seasons,
        'can_watch': can_watch,
        'plan': plan,
        'can_review': can_review,
        'reviews': reviews,
        'user_review': user_review,
        'avg_rating': avg_rating,
        'trailer_youtube_id': extract_youtube_id(movie.trailer_url),
    })

@login_required(login_url='/users/login/')
def watchlist_toggle(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        watchlist_item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='/users/login/')
def watchlist_view(request):
    items = Watchlist.objects.filter(user=request.user)
    return render(request, 'movies/watchlist.html', {'items': items})

@login_required(login_url='/users/login/')
def player_view(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    plan = get_user_plan(request.user)
    if TIER_LEVEL.get(plan, 0) < TIER_LEVEL.get(movie.tier, 0):
        return redirect('membresias')
    return render(request, 'movies/player.html', {'movie': movie})

@login_required(login_url='/users/login/')
def membresias(request):
    plan = get_user_plan(request.user)
    return render(request, 'movies/membresias.html', {'plan': plan})

@login_required(login_url='/users/login/')
def pago(request):
    if request.method == 'POST':
        codigo = request.POST.get('plan')

        # Validación server-side: solo se aceptan planes de la lista blanca.
        # Cualquier 'precio' que venga del cliente se ignora por completo.
        if codigo not in PLANES:
            messages.error(request, 'Plan inválido.')
            return redirect('membresias')

        try:
            membership, _ = Membership.objects.get_or_create(user=request.user)
            membership.plan = codigo
            membership.status = 'pending'
            membership.save()
        except Exception as e:
            logger.error(f'Error al registrar membresía para {request.user}: {e}')
            messages.error(request, 'Hubo un problema al procesar el pago. Intentá de nuevo.')
            return redirect('membresias')

        return render(request, 'movies/pago.html', {
            'nombre': PLANES[codigo]['nombre'],
            'precio': PLANES[codigo]['precio'],
            'codigo': codigo,
            'success': True,
        })

    codigo = request.GET.get('plan', 'medium')
    if codigo not in PLANES:
        codigo = 'medium'

    return render(request, 'movies/pago.html', {
        'nombre': PLANES[codigo]['nombre'],
        'precio': PLANES[codigo]['precio'],
        'codigo': codigo,
        'success': False,
    })

@login_required(login_url='/users/login/')
def episode_player(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    plan = get_user_plan(request.user)
    if TIER_LEVEL.get(plan, 0) < TIER_LEVEL.get(episode.season.series.tier, 0):
        return redirect('membresias')
    return render(request, 'movies/episode_player.html', {'episode': episode})


@login_required(login_url='/users/login/')
def review_submit(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    plan = get_user_plan(request.user)

    if plan not in TIERS_CON_REVIEWS:
        return redirect('movie_detail', pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and comment:
            Review.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'rating': int(rating), 'comment': comment}
            )

    return redirect('movie_detail', pk=pk)

@login_required(login_url='/users/login/')
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    movie_pk = review.movie.pk
    review.delete()
    return redirect('movie_detail', pk=movie_pk)


@login_required(login_url='/users/login/')
def catalogo(request, tipo):
    # Solo 'movie' o 'series'; cualquier otra cosa es una URL que no existe.
    if tipo not in (Movie.MOVIE, Movie.SERIES):
        raise Http404('Tipo de catálogo inválido.')

    resultados = Movie.objects.filter(type=tipo)

    # Búsqueda por título (parcial, case-insensitive).
    q = request.GET.get('q', '').strip()
    if q:
        resultados = resultados.filter(title__icontains=q)

    # Filtros opcionales y combinables entre sí.
    genero = request.GET.get('genero', '').strip()
    if genero:
        resultados = resultados.filter(genres__name=genero)

    anio = request.GET.get('anio', '').strip()
    if anio.isdigit():
        # year es IntegerField: si viene basura no numérica ignoramos el
        # filtro en vez de crashear con ValueError.
        resultados = resultados.filter(year=int(anio))

    tier = request.GET.get('tier', '').strip()
    if tier in TIER_LEVEL:
        resultados = resultados.filter(tier=tier)

    # Ordenamiento server-side.
    orden = request.GET.get('orden', '').strip()
    if orden == 'rating':
        resultados = resultados.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif orden in CATALOGO_ORDEN:
        resultados = resultados.order_by(CATALOGO_ORDEN[orden])
    else:
        resultados = resultados.order_by('-id')

    # El filtro M2M por género puede duplicar filas; distinct() lo evita.
    resultados = resultados.distinct()

    plan = get_user_plan(request.user)

    return render(request, 'movies/catalogo.html', {
        'resultados': resultados,
        'genres': Genre.objects.all(),
        'tipo': tipo,
        'plan': plan,
    })
