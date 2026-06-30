import os
import tempfile
from io import BytesIO

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from PIL import Image

from users.models import Membership

User = get_user_model()


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


def _jpeg_bytes(size):
    """Devuelve un JPEG válido (color sólido, comprime chiquito) de NxN px."""
    buf = BytesIO()
    Image.new('RGB', size, (90, 120, 200)).save(buf, format='JPEG')
    return buf.getvalue()


def _heavy_png_bytes(size):
    """PNG de ruido aleatorio: incompresible, así supera fácil los 128KB."""
    buf = BytesIO()
    noise = Image.frombytes('RGB', size, os.urandom(size[0] * size[1] * 3))
    noise.save(buf, format='PNG')
    return buf.getvalue()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AvatarUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        # perfil_editar redirige a los free; necesitamos un plan pago activo.
        Membership.objects.create(user=self.user, plan='medium', status='active')
        self.client.login(username='testuser', password='pass1234')
        self.url = '/users/perfil/editar/'

    def _upload(self, content, filename, content_type):
        from django.core.files.uploadedfile import SimpleUploadedFile
        avatar = SimpleUploadedFile(filename, content, content_type=content_type)
        return self.client.post(
            self.url,
            {'display_name': 'Test', 'avatar': avatar},
            follow=True,
        )

    def test_valid_avatar_is_saved(self):
        content = _jpeg_bytes((128, 128))
        self.assertLess(len(content), 128 * 1024)
        response = self._upload(content, 'avatar.jpg', 'image/jpeg')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_oversized_avatar_is_rejected(self):
        content = _heavy_png_bytes((512, 512))
        self.assertGreater(len(content), 128 * 1024)
        response = self._upload(content, 'avatar.png', 'image/png')
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)
        messages = list(response.context['messages'])
        self.assertTrue(any(m.level_tag == 'error' for m in messages))

    def test_wrong_dimensions_are_rejected(self):
        content = _jpeg_bytes((64, 64))
        self.assertLess(len(content), 128 * 1024)
        response = self._upload(content, 'avatar.jpg', 'image/jpeg')
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)
        messages = list(response.context['messages'])
        self.assertTrue(any(m.level_tag == 'error' for m in messages))
