from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.users.forms import RegisterForm


class UserTestCase(TestCase):
    def test_register_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, 'newuser')

    def test_get_absolute_url(self):
        user = User.objects.create_user(username='testurluser', password='password123')
        self.assertEqual(user.get_absolute_url(), reverse('users:profile', kwargs={'username': 'testurluser'}))
