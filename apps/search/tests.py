from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='TestCommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Test content',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts_tab(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'tab': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['posts'])

    def test_search_results_communities_tab(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'tab': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['communities'])

    def test_search_results_users_tab(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'tab': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, response.context['users'])

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['title'] == 'Test Post Title' for s in suggestions))
        self.assertTrue(any(s['title'] == 'TestCommunity' for s in suggestions))
