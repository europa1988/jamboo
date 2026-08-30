from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.posts.models import Post
from apps.communities.models import Community


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.profile.bio = 'Test user bio'
        self.user.profile.save()
        self.community = Community.objects.create(name='testcommunity', slug='testcommunity', description='Test community', creator=self.user)
        self.post = Post.objects.create(title='Test Post Title', slug='test-post-title', content='Test post content', author=self.user, community=self.community)

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post Title')

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testcommunity')

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post Title')
