from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user2 = User.objects.create_user(username='otheruser', password='password123')

        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='A test community',
            creator=self.user
        )

        self.post = Post.objects.create(
            title='Test Search Post',
            slug='test-search-post',
            content='Some content for search testing',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        self.client.force_login(self.user)
        UserFollow.objects.create(follower=self.user, following=self.user2)
        response = self.client.get(reverse('search:results'), {'q': 'otheruser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertTrue(getattr(results[0], 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))
        self.assertTrue(any(s['type'] == 'user' for s in suggestions))
