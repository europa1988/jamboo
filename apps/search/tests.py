from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='Password123!'
        )
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Test post content body',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 1)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
        self.assertIn('user', types)
