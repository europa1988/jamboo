from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.forms import RegisterForm

User = get_user_model()


class UsersTestCase(TestCase):
    def test_user_get_absolute_url(self):
        user = User.objects.create_user(username='testuser', password='password123')
        self.assertEqual(user.get_absolute_url(), '/u/testuser/')

    def test_profile_creation_signal(self):
        user = User.objects.create_user(username='profileuser', password='password123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.user, user)

    def test_register_form_fields(self):
        form = RegisterForm()
        self.assertIn('username', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)
        self.assertEqual(list(form.Meta.fields), ['username', 'email'])

    def test_user_follow_view(self):
        user1 = User.objects.create_user(username='u1', password='password123')
        user2 = User.objects.create_user(username='u2', password='password123')
        self.client.login(username='u1', password='password123')

        follow_url = reverse('users:follow', kwargs={'username': 'u2'})
        res = self.client.post(follow_url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(user1.following.filter(following=user2).exists())

        # Unfollow
        res = self.client.post(follow_url)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(user1.following.filter(following=user2).exists())
