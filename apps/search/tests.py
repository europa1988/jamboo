from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Search Post',
            content='This is a post for testing search.',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Search Post')

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/testcommunity')

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testuser')

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Search'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Search Post')
