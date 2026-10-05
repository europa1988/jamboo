from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Python testing in Django',
            content='This is a test post content.',
            author=self.user,
            community=self.community,
            slug='python-testing-in-django'
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcomm', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'community' and 'testcommunity' in s['title'] for s in suggestions))
        self.assertTrue(any(s['type'] == 'user' and 'testuser' in s['title'] for s in suggestions))

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
