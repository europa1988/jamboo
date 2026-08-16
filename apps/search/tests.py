from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=50)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=100)

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1,
            member_count=10
        )

        self.post1 = Post.objects.create(
            title='Python Tutorial for Beginners',
            slug='python-tutorial-for-beginners',
            content='Learn Python basics',
            author=self.user1,
            community=self.community
        )

        self.post2 = Post.objects.create(
            title='Python Web Development Guide with Django',
            slug='python-web-development-guide-with-django',
            content='Build websites with Django and Python',
            author=self.user2,
            community=self.community
        )

        PostVote.objects.create(user=self.user1, post=self.post1, value=1)

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['total_count'], 2)

    def test_search_results_authenticated_user_vote(self):
        self.client.login(username='alice', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Tutorial', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'pyth', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'ali', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_short_query_error(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'a', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])

    def test_search_suggestions_htmx(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
