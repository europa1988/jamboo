from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import UserFollow
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Django and Python community',
            creator=self.user1,
            member_count=10
        )

        self.post = Post.objects.create(
            title='Django Search Implementation',
            slug='django-search-implementation',
            content='Testing search in Jamboo project',
            author=self.user1,
            community=self.community
        )

        UserFollow.objects.create(follower=self.user1, following=self.user2)
        PostVote.objects.create(user=self.user1, post=self.post, value=1)

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')
        self.assertEqual(response.context['total_count'], 0)

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_authenticated_post_vote(self):
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser2', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        users = list(response.context['results'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_following)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
