from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123'
        )

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python developers community',
            creator=self.user1
        )

        self.post = Post.objects.create(
            title='Python 3.12 Features',
            slug='python-312-features',
            content='Awesome new features in Python',
            author=self.user1,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        self.client.force_login(self.user1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        found_user = response.context['results'][0]
        self.assertEqual(found_user, self.user2)
        self.assertTrue(getattr(found_user, 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)
        types = [item['type'] for item in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
