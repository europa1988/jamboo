from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.users.forms import RegisterForm


class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )

    def test_user_get_absolute_url(self):
        expected_url = reverse('users:profile', kwargs={'username': 'user1'})
        self.assertEqual(self.user.get_absolute_url(), expected_url)

    def test_user_profile_automatically_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_register_form_valid(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
