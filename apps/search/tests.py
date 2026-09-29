from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1,
            is_active=True
        )

        self.post = Post.objects.create(
            title='Django Search Tutorial',
            content='How to implement search in Django',
            author=self.user1,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Search Tutorial')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/python')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testuser1')
        self.assertEqual(response.context['total_count'], 2)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
        item = suggestions[0]
        self.assertIn('url', item)
        self.assertIn('type', item)
        self.assertIn('title', item)
        self.assertIn('subtitle', item)
