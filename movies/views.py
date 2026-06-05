from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Movie, Genre, Watchlist, Season, Episode
from users.models import Membership

@login_required(login_url='/users/login/')
def home(request):
    try:
        membership = Membership.objects.get(user=request.user)
        plan = membership.plan if membership.status == 'active' else 'free'
    except Membership.DoesNotExist:
        plan = 'free'

    movies = Movie.objects.filter(type='movie')
    series = Movie.objects.filter(type='series')
    genres = Genre.objects.all()
    featured_movies = Movie.objects.filter(featured=True)

    return render(request, 'movies/home.html', {
        'movies': movies,
        'series': series,
        'genres': genres,
        'featured_movies': featured_movies,
        'plan': plan,
    })

@login_required(login_url='/users/login/')
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    seasons = movie.seasons.prefetch_related('episodes').all() if movie.type == 'series' else None

    try:
        membership = Membership.objects.get(user=request.user)
        plan = membership.plan if membership.status == 'active' else 'free'
    except Membership.DoesNotExist:
        plan = 'free'

    tier_required = {'free': 0, 'medium': 1, 'premium': 2}
    user_level = tier_required.get(plan, 0)
    movie_level = tier_required.get(movie.tier, 0)

    can_watch = user_level >= movie_level

    return render(request, 'movies/detail.html', {
        'movie': movie,
        'in_watchlist': in_watchlist,
        'seasons': seasons,
        'can_watch': can_watch,
        'plan': plan,
    })

@login_required(login_url='/users/login/')
def watchlist_toggle(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    watchlist_item, created = Watchlist.objects.get_or_create(
        user=request.user,
        movie=movie
    )
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
    return render(request, 'movies/player.html', {'movie': movie})

@login_required(login_url='/users/login/')
def membresias(request):
    return render(request, 'movies/membresias.html')

@login_required(login_url='/users/login/')
def pago(request):
    plan = request.GET.get('plan', 'Cinephile')
    precio = request.GET.get('precio', '2.99')

    if request.method == 'POST':
        plan_nombre = request.POST.get('plan', 'Cinephile')
        plan_map = {'Cinephile': 'medium', 'Ultra': 'premium', 'Zerpanito': 'zerpanito'}
        plan_code = plan_map.get(plan_nombre, 'medium')

        membership, created = Membership.objects.get_or_create(user=request.user)
        membership.plan = plan_code
        membership.status = 'pending'
        membership.save()

        return render(request, 'movies/pago.html', {
            'plan': plan_nombre,
            'precio': precio,
            'success': True,
        })

    return render(request, 'movies/pago.html', {
        'plan': plan,
        'precio': precio,
        'success': False,
    })

@login_required(login_url='/users/login/')
def episode_player(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    return render(request, 'movies/episode_player.html', {'episode': episode})
