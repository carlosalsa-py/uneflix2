from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Movie, Genre, Watchlist, Episode, Review
from users.models import Membership

TIER_LEVEL = {'free': 0, 'medium': 1, 'premium': 2}

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
    plan = request.GET.get('plan', 'Cinéfilo')
    precio = request.GET.get('precio', '2.99')

    if request.method == 'POST':
        plan_nombre = request.POST.get('plan', 'Cinéfilo')
        plan_map = {'Cinéfilo': 'medium', 'Zerpanito': 'premium'}
        plan_code = plan_map.get(plan_nombre, 'medium')

        membership, _ = Membership.objects.get_or_create(user=request.user)
        membership.plan = plan_code
        membership.status = 'pending'
        membership.save()

        return render(request, 'movies/pago.html', {
            'plan': plan_nombre,
            'precio': precio,
            'success': True,
        })

    return render(request, 'movies/pago.html', {'plan': plan, 'precio': precio, 'success': False})

@login_required(login_url='/users/login/')
def episode_player(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    plan = get_user_plan(request.user)
    if TIER_LEVEL.get(plan, 0) < TIER_LEVEL.get(episode.season.series.tier, 0):
        return redirect('membresias')
    return render(request, 'movies/episode_player.html', {'episode': episode})


def anuncio(request, num):
    return render(request, f'movies/anuncio{num}.html')

@login_required(login_url='/users/login/')
def review_submit(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    plan = get_user_plan(request.user)

    if plan not in ('medium', 'premium', 'zerpanito'):
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
