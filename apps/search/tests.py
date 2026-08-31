from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user,
            member_count=5
        )

        self.post1 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312-release-notes',
            content='Awesome new features in Python 3.12',
            author=self.user,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Learning Django framework',
            slug='learning-django-framework',
            content='Guide to building web apps with Django',
            author=self.user,
            community=self.community
        )

        PostVote.objects.create(user=self.user, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user, following=self.other_user)

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пожалуйста, введите поисковый запрос.')

    def test_search_results_posts_unauthenticated(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post1, response.context['results'])

    def test_search_results_posts_authenticated(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'otheruser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.other_user)
        self.assertTrue(getattr(results[0], 'is_following', False))

    def test_search_suggestions_empty(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_populated(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
        post_suggestion = next((item for item in suggestions if item['type'] == 'post'), None)
        self.assertIsNotNone(post_suggestion)
        self.assertIn('Python 3.12 release notes', post_suggestion['title'])
