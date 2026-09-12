from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.communities.models import Community
from apps.posts.models import Post

User = get_user_model()


class SearchViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='searcheduser',
            email='searched@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Django test post',
            content='Testing search functionality in Django',
            author=self.user,
            community=self.community
        )

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')
        self.assertIsNone(response.context['results'])

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post, response.context['results'].object_list)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community, response.context['results'].object_list)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'searched', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.other_user, response.context['results'].object_list)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        post_suggestion = next((s for s in suggestions if s['type'] == 'post'), None)
        self.assertIsNotNone(post_suggestion)
        self.assertEqual(post_suggestion['title'], 'Django test post')
