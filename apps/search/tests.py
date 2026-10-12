from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Django 6 tutorial',
            content='Awesome web framework',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertEqual(len(response.context['suggestions']), 1)
        self.assertEqual(response.context['suggestions'][0]['title'], 'Django 6 tutorial')
