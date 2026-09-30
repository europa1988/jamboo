from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123', karma=10)
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            creator=self.user,
            description='A test community description'
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            content='Test Post Content',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post Title')

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/testcommunity')

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testuser')

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post Title')
