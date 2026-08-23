from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Test post content',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post Title')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/testcommunity')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testuser')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' and 'Test Post Title' in s['title'] for s in suggestions))
