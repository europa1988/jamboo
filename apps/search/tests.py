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
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
            first_name='Alice'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123',
            first_name='Bob'
        )
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python developers community',
            creator=self.user1,
            member_count=10
        )
        self.post = Post.objects.create(
            title='Django 6 features in Python',
            slug='django-6-features-in-python',
            content='Discussion about new features in Django and Python',
            author=self.user1,
            community=self.community
        )

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_short_query(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Запрос должен содержать минимум 2 символа')

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_posts_authenticated_with_vote(self):
        PostVote.objects.create(user=self.user2, post=self.post, value=1)
        self.client.login(username='bob', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user2, following=self.user1)
        self.client.login(username='bob', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = list(response.context['results'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_following)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
