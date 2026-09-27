from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(name='Test Community', slug='test-comm', creator=self.user)
        self.post = Post.objects.create(
            title='Test Post Title',
            content='Some content here',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Community', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, response.context['results'])

    def test_search_results_short_query(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertTrue(len(response.context['suggestions']) > 0)
