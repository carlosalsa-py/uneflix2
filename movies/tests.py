from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Movie, Watchlist, Review
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
