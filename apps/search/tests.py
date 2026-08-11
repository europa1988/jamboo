from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.users.models import UserFollow


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create users
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='jamboouser', password='password123')

        # Create community
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Community for testing search',
            creator=self.user1,
            is_active=True
        )

        # Create post
        self.post = Post.objects.create(
            title='Welcome to Jamboo!',
            slug='welcome-to-jamboo',
            content='This is a testing post content for search validation.',
            author=self.user1,
            community=self.community,
            is_deleted=False
        )

    def test_search_posts_unauthenticated(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Jamboo', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(response.context['query'], 'Jamboo')
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)
        self.assertIsNone(response.context['results'][0].user_vote)

    def test_search_posts_authenticated(self):
        # Authenticate user2
        self.client.login(username='jamboouser', password='password123')

        # Create a vote for the post
        PostVote.objects.create(user=self.user2, post=self.post, value=PostVote.UPVOTE)

        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Jamboo', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0].user_vote, PostVote.UPVOTE)

    def test_search_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcomm', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'jamboo', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user2)

    def test_search_users_authenticated_following(self):
        self.client.login(username='testuser1', password='password123')

        # Follow user2
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        url = reverse('search:results')
        response = self.client.get(url, {'q': 'jamboo', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertTrue(response.context['results'][0].is_following)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'jam'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)

        # Verify suggestions have correct keys
        for suggestion in suggestions:
            self.assertIn('url', suggestion)
            self.assertIn('type', suggestion)
            self.assertIn('title', suggestion)
            self.assertIn('subtitle', suggestion)

    def test_search_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])
