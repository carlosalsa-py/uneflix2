from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Movie, Genre, Watchlist, Season, Episode

@login_required(login_url='/users/login/')
def home(request):
    movies = Movie.objects.filter(type='movie')
    series = Movie.objects.filter(type='series')
    genres = Genre.objects.all()
    featured_movies = Movie.objects.filter(featured=True)
    return render(request, 'movies/home.html', {
        'movies': movies,
        'series': series,
        'genres': genres,
        'featured_movies': featured_movies,
    })

@login_required(login_url='/users/login/')
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    seasons = movie.seasons.prefetch_related('episodes').all() if movie.type == 'series' else None
    return render(request, 'movies/detail.html', {
        'movie': movie,
        'in_watchlist': in_watchlist,
        'seasons': seasons,
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
    return render(request, 'movies/pago.html')

@login_required(login_url='/users/login/')
def episode_player(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    return render(request, 'movies/episode_player.html', {'episode': episode})