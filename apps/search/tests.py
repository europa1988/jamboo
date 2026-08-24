from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote

class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            creator=self.user1,
            is_active=True
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Some content here',
            author=self.user1,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['results'])
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        self.client.force_login(self.user1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        response = self.client.get(reverse('search:results'), {'q': 'testuser2', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_following)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 1)
