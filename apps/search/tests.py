from django.test import TestCase
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User


class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Some test post content',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcomm', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertTrue(len(response.context['suggestions']) > 0)
