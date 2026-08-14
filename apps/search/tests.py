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
        self.author = User.objects.create_user(
            username='authoruser',
            password='Password123!'
        )
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='A community for testing search',
            creator=self.author
        )
        self.post1 = Post.objects.create(
            title='Python Django search testing',
            slug='python-django-search-testing',
            content='This is a test post content about Django.',
            author=self.author,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Another topic post',
            slug='another-topic-post',
            content='Nothing related to snake language.',
            author=self.author,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testing', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'author', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.author)

    def test_search_suggestions_endpoint(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 1)
        # Check structure of items
        for item in suggestions:
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn('url', item)
