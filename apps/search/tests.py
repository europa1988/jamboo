from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='john_doe', password='password123')

        self.community = Community.objects.create(
            name='python_devs',
            slug='python_devs',
            description='Python developers community',
            creator=self.user,
            is_active=True
        )

        self.post1 = Post.objects.create(
            title='Django 6 release features',
            slug='django-6-release-features',
            content='Awesome features in Django 6',
            author=self.user,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 performance',
            slug='python-312-performance',
            content='Fast execution times',
            author=self.other_user,
            community=self.community
        )

        PostVote.objects.create(user=self.user, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user, following=self.other_user)

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)

    def test_search_results_authenticated_user_votes(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post2)
        self.assertEqual(results[0].user_vote, 0)

        response2 = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        results2 = response2.context['results']
        self.assertEqual(results2[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community)

    def test_search_results_users(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'john', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.other_user)
        self.assertTrue(results[0].is_following)

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 0)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
