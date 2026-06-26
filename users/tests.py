from django.test import TestCase, Client


class AcceptTermsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_is_not_allowed(self):
        response = self.client.get('/users/terms/accept/')
        self.assertEqual(response.status_code, 405)

    def test_get_does_not_set_session_flag(self):
        self.client.get('/users/terms/accept/')
        self.assertNotIn('accepted_terms', self.client.session)

    def test_post_accepts_terms_and_redirects(self):
        response = self.client.post('/users/terms/accept/')
        self.assertRedirects(response, '/users/register/')
        self.assertTrue(self.client.session.get('accepted_terms'))
