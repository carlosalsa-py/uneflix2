import tempfile
from datetime import timedelta

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
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


class ViewCountTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewer', password='pass1234')
        self.client.login(username='viewer', password='pass1234')
        self.movie = Movie.objects.create(title='Contada', tier='free', type='movie',
                                          year=2020, description='x')

    def test_detail_increments_views(self):
        self.assertEqual(self.movie.views, 0)
        self.client.get(f'/movie/{self.movie.pk}/')
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.views, 1)
        self.client.get(f'/movie/{self.movie.pk}/')
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.views, 2)


class SidebarTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='home', password='pass1234')
        self.client.login(username='home', password='pass1234')
        self.today = timezone.localdate()

    def _home(self):
        return self.client.get('/')

    def test_mas_vistas_ordered_and_excludes_zero(self):
        pop = Movie.objects.create(title='Popular', tier='free', type='movie', year=2020,
                                   description='x', views=50)
        mid = Movie.objects.create(title='Media', tier='free', type='movie', year=2020,
                                   description='x', views=5)
        Movie.objects.create(title='Nunca Vista', tier='free', type='movie', year=2020,
                             description='x', views=0)
        ctx = self._home().context
        titles = [m.title for m in ctx['mas_vistas']]
        self.assertEqual(titles, ['Popular', 'Media'])  # ordenadas desc, sin la de 0 vistas
        self.assertNotIn('Nunca Vista', titles)

    def test_mejor_rateadas_ordered_by_avg(self):
        u2 = User.objects.create_user(username='critico', password='pass1234')
        alta = Movie.objects.create(title='Obra Maestra', tier='free', type='movie', year=2020, description='x')
        baja = Movie.objects.create(title='Mala', tier='free', type='movie', year=2020, description='x')
        sin = Movie.objects.create(title='Sin Reseñas', tier='free', type='movie', year=2020, description='x')
        Review.objects.create(movie=alta, user=self.user, rating=5, comment='top')
        Review.objects.create(movie=alta, user=u2, rating=5, comment='top')
        Review.objects.create(movie=baja, user=self.user, rating=1, comment='meh')
        ctx = self._home().context
        titles = [m.title for m in ctx['mejor_rateadas']]
        self.assertEqual(titles, ['Obra Maestra', 'Mala'])  # 5.0 antes que 1.0
        self.assertNotIn('Sin Reseñas', titles)  # las sin reseñas no aparecen

    def test_proximos_estrenos_only_future_ascending(self):
        pronto = Movie.objects.create(title='Pronto', tier='free', type='movie', year=2027,
                                      description='x', release_date=self.today + timedelta(days=3))
        lejos = Movie.objects.create(title='Lejos', tier='free', type='movie', year=2027,
                                     description='x', release_date=self.today + timedelta(days=30))
        Movie.objects.create(title='Ya Salio', tier='free', type='movie', year=2019,
                             description='x', release_date=self.today - timedelta(days=10))
        Movie.objects.create(title='Sin Fecha', tier='free', type='movie', year=2020, description='x')
        ctx = self._home().context
        titles = [m.title for m in ctx['proximos_estrenos']]
        self.assertEqual(titles, ['Pronto', 'Lejos'])  # fecha futura, ascendente
        self.assertNotIn('Ya Salio', titles)
        self.assertNotIn('Sin Fecha', titles)

    def test_empty_states_render(self):
        # Sin datos, la home igual responde 200 y muestra los empty-states.
        response = self._home()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aún no hay reproducciones')
        self.assertContains(response, 'Aún no hay reseñas')
        self.assertContains(response, 'Sin estrenos programados')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MovieVideoUrlTest(TestCase):
    """SPEC 007: el reproductor debe usar video_url como fallback cuando no hay
    video_file, y video_file debe tener prioridad cuando ambos están."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='player', password='pass1234')
        self.client.login(username='player', password='pass1234')

    def test_video_url_renders_iframe(self):
        movie = Movie.objects.create(
            title='Nosferatu', tier='free', type='movie', year=1922, description='x',
            video_url='https://archive.org/embed/nosferatu_1922',
        )
        response = self.client.get(f'/movie/{movie.pk}/play/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<iframe')
        self.assertContains(response, 'https://archive.org/embed/nosferatu_1922')

    def test_video_file_takes_priority(self):
        movie = Movie.objects.create(
            title='Con Archivo', tier='free', type='movie', year=2020, description='x',
            video_file=SimpleUploadedFile('clip.mp4', b'fakebytes', content_type='video/mp4'),
            video_url='https://archive.org/embed/algo',
        )
        response = self.client.get(f'/movie/{movie.pk}/play/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<video')          # prioriza el archivo local
        self.assertNotContains(response, '<iframe')       # no cae al fallback

    def test_no_source_still_renders(self):
        # Sin video_file ni video_url el player no debe romperse (200, sin iframe/video).
        movie = Movie.objects.create(title='Sin Video', tier='free', type='movie',
                                     year=2020, description='x')
        response = self.client.get(f'/movie/{movie.pk}/play/')
        self.assertEqual(response.status_code, 200)

    def test_clean_rejects_archive_details_url(self):
        movie = Movie(title='Mala URL', tier='free', type='movie', year=1922, description='x',
                      video_url='https://archive.org/details/nosferatu_1922')
        with self.assertRaises(ValidationError):
            movie.full_clean()

    def test_clean_accepts_archive_embed_url(self):
        movie = Movie(title='Buena URL', tier='free', type='movie', year=1922, description='x',
                      video_url='https://archive.org/embed/nosferatu_1922')
        # No debe lanzar por el video_url (el embed es válido).
        try:
            movie.full_clean()
        except ValidationError as e:
            self.assertNotIn('video_url', e.message_dict)
