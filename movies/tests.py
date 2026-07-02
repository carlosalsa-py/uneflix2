from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Movie, Genre, Watchlist, Review
from .views import extract_youtube_id
from users.models import Membership

User = get_user_model()


class TierAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.free_movie = Movie.objects.create(title='Free Film', tier='free', type='movie', year=2020, description='Test')
        self.premium_movie = Movie.objects.create(title='Premium Film', tier='premium', type='movie', year=2020, description='Test')

    def test_free_user_can_play_free_content(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(f'/movie/{self.free_movie.pk}/play/')
        self.assertEqual(response.status_code, 200)

    def test_free_user_cannot_play_premium_content(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(f'/movie/{self.premium_movie.pk}/play/')
        self.assertRedirects(response, '/membresias/')

    def test_premium_user_can_play_premium_content(self):
        Membership.objects.create(user=self.user, plan='premium', status='active')
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(f'/movie/{self.premium_movie.pk}/play/')
        self.assertEqual(response.status_code, 200)

    def test_inactive_membership_treated_as_free(self):
        Membership.objects.create(user=self.user, plan='premium', status='pending')
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(f'/movie/{self.premium_movie.pk}/play/')
        self.assertRedirects(response, '/membresias/')


class WatchlistTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.movie = Movie.objects.create(title='Test Film', tier='free', type='movie', year=2020, description='Test')

    def test_toggle_adds_to_watchlist(self):
        self.client.login(username='testuser', password='pass1234')
        self.client.post(f'/movie/{self.movie.pk}/watchlist/')
        self.assertTrue(Watchlist.objects.filter(user=self.user, movie=self.movie).exists())

    def test_toggle_removes_from_watchlist(self):
        Watchlist.objects.create(user=self.user, movie=self.movie)
        self.client.login(username='testuser', password='pass1234')
        self.client.post(f'/movie/{self.movie.pk}/watchlist/')
        self.assertFalse(Watchlist.objects.filter(user=self.user, movie=self.movie).exists())


class ReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.movie = Movie.objects.create(title='Test Film', tier='free', type='movie', year=2020, description='Test')

    def test_free_user_cannot_submit_review(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.post(f'/movie/{self.movie.pk}/review/', {'rating': 5, 'comment': 'Great!'})
        self.assertRedirects(response, f'/movie/{self.movie.pk}/')
        self.assertFalse(Review.objects.filter(user=self.user, movie=self.movie).exists())

    def test_paid_user_can_submit_review(self):
        Membership.objects.create(user=self.user, plan='medium', status='active')
        self.client.login(username='testuser', password='pass1234')
        self.client.post(f'/movie/{self.movie.pk}/review/', {'rating': 4, 'comment': 'Good movie'})
        self.assertTrue(Review.objects.filter(user=self.user, movie=self.movie).exists())

    def test_premium_user_can_submit_review(self):
        Membership.objects.create(user=self.user, plan='premium', status='active')
        self.client.login(username='testuser', password='pass1234')
        self.client.post(f'/movie/{self.movie.pk}/review/', {'rating': 5, 'comment': 'Excellent'})
        self.assertTrue(Review.objects.filter(user=self.user, movie=self.movie).exists())


class PagoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.client.login(username='testuser', password='pass1234')

    def test_valid_plan_creates_pending_membership(self):
        response = self.client.post('/pago/', {'plan': 'medium'})
        self.assertEqual(response.status_code, 200)
        membership = Membership.objects.get(user=self.user)
        self.assertEqual(membership.plan, 'medium')
        self.assertEqual(membership.status, 'pending')

    def test_invalid_plan_is_rejected(self):
        response = self.client.post('/pago/', {'plan': 'hack'})
        self.assertRedirects(response, '/membresias/')
        self.assertFalse(Membership.objects.filter(user=self.user).exists())

    def test_client_price_is_ignored(self):
        # Aunque el cliente mande un precio adulterado, el backend usa el suyo
        # y nunca persiste el precio del POST.
        self.client.post('/pago/', {'plan': 'premium', 'precio': '0.01'})
        membership = Membership.objects.get(user=self.user)
        self.assertEqual(membership.plan, 'premium')


class CatalogoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.client.login(username='testuser', password='pass1234')

        self.accion = Genre.objects.create(name='Acción')
        self.drama = Genre.objects.create(name='Drama')

        self.alpha = Movie.objects.create(title='Alpha', type='movie', year=2020, tier='free', description='x')
        self.alpha.genres.add(self.accion)

        self.beta = Movie.objects.create(title='Beta Movie', type='movie', year=2021, tier='premium', description='x')
        self.beta.genres.add(self.drama)

        self.gamma = Movie.objects.create(title='Gamma Alpha', type='movie', year=2020, tier='medium', description='x')
        self.gamma.genres.add(self.accion)

        self.serie = Movie.objects.create(title='Serie Uno', type='series', year=2019, tier='free', description='x')
        self.serie.genres.add(self.drama)

    def _titles(self, response):
        return set(response.context['resultados'].values_list('title', flat=True))

    def test_movie_type_returns_only_movies(self):
        response = self.client.get('/catalogo/movie/')
        self.assertEqual(self._titles(response), {'Alpha', 'Beta Movie', 'Gamma Alpha'})

    def test_series_type_returns_only_series(self):
        response = self.client.get('/catalogo/series/')
        self.assertEqual(self._titles(response), {'Serie Uno'})

    def test_q_matches_partial_case_insensitive(self):
        response = self.client.get('/catalogo/movie/', {'q': 'alpha'})
        self.assertEqual(self._titles(response), {'Alpha', 'Gamma Alpha'})

    def test_genero_filter(self):
        response = self.client.get('/catalogo/movie/', {'genero': 'Acción'})
        self.assertEqual(self._titles(response), {'Alpha', 'Gamma Alpha'})

    def test_anio_filter(self):
        response = self.client.get('/catalogo/movie/', {'anio': '2020'})
        self.assertEqual(self._titles(response), {'Alpha', 'Gamma Alpha'})

    def test_tier_filter(self):
        response = self.client.get('/catalogo/movie/', {'tier': 'premium'})
        self.assertEqual(self._titles(response), {'Beta Movie'})

    def test_combined_genero_and_tier(self):
        # Acción tiene Alpha (free) y Gamma Alpha (medium); sumar tier=medium
        # debe dejar solo Gamma Alpha.
        response = self.client.get('/catalogo/movie/', {'genero': 'Acción', 'tier': 'medium'})
        self.assertEqual(self._titles(response), {'Gamma Alpha'})

    def test_orden_titulo_asc_is_alphabetical(self):
        response = self.client.get('/catalogo/movie/', {'orden': 'titulo_asc'})
        titles = list(response.context['resultados'].values_list('title', flat=True))
        self.assertEqual(titles, ['Alpha', 'Beta Movie', 'Gamma Alpha'])

    def test_invalid_tipo_returns_404(self):
        response = self.client.get('/catalogo/comida/')
        self.assertEqual(response.status_code, 404)


class ExtractYoutubeIdTest(TestCase):
    ID = 'dQw4w9WgXcQ'

    def test_common_url_formats(self):
        urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ?si=Ab12Cd34',           # botón Compartir
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s',
            'https://www.youtube.com/watch?list=PLxyz&v=dQw4w9WgXcQ',  # v no primero
            'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://music.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/embed/dQw4w9WgXcQ',
            'https://www.youtube.com/shorts/dQw4w9WgXcQ',
            'dQw4w9WgXcQ',                                          # ID pelado
            '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>',  # código Insertar
        ]
        for url in urls:
            self.assertEqual(extract_youtube_id(url), self.ID, msg=url)

    def test_non_youtube_returns_none(self):
        for value in ['https://vimeo.com/74489527', 'https://example.com/x', '', None, 'no soy una url']:
            self.assertIsNone(extract_youtube_id(value), msg=repr(value))


class TrailerRenderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.client.login(username='testuser', password='pass1234')

    def _detail(self, movie):
        return self.client.get(f'/movie/{movie.pk}/')

    def test_youtube_trailer_renders_iframe(self):
        movie = Movie.objects.create(title='Con Trailer', tier='free', type='movie', year=2020,
                                     description='x', trailer_url='https://youtu.be/dQw4w9WgXcQ')
        response = self._detail(movie)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://www.youtube.com/embed/dQw4w9WgXcQ')
        # referrerpolicy evita el Error 153 de YouTube: Django manda
        # Referrer-Policy: same-origin, que sin esto no enviaría Referer al
        # iframe cross-origin y el reproductor no valida el origen.
        self.assertContains(response, 'referrerpolicy="strict-origin-when-cross-origin"')

    def test_non_youtube_trailer_does_not_break_page(self):
        # Una URL no-YouTube (o basura) no debe romper la página: el trailer
        # simplemente no se muestra, en vez de tirar 500 como hacía embed_video.
        movie = Movie.objects.create(title='Trailer Vimeo', tier='free', type='movie', year=2020,
                                     description='x', trailer_url='https://vimeo.com/74489527')
        response = self._detail(movie)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'youtube.com/embed')

    def test_no_trailer_url(self):
        movie = Movie.objects.create(title='Sin Trailer', tier='free', type='movie', year=2020,
                                     description='x')
        response = self._detail(movie)
        self.assertEqual(response.status_code, 200)
