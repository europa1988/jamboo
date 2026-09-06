from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.forms import RegisterForm

User = get_user_model()


class UserTestCase(TestCase):
    def test_user_profile_created_and_absolute_url(self):
        user = User.objects.create_user(username='charlie', email='charlie@example.com', password='password123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.get_absolute_url(), reverse('users:profile', kwargs={'username': 'charlie'}))

    def test_register_form_fields(self):
        form = RegisterForm()
        self.assertIn('username', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)
        self.assertEqual(list(form.Meta.fields), ['username', 'email'])
