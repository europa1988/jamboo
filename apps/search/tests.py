from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


class SearchTests(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='alice_wonder',
            email='alice@example.com',
            password='password123',
            karma=100
        )
        self.user2 = User.objects.create_user(
            username='bob_builder',
            email='bob@example.com',
            password='password123',
            karma=50
        )

        # Create communities
        self.community_active = Community.objects.create(
            name='django_dev',
            slug='django_dev',
            description='Community for Django developers.',
            creator=self.user1,
            is_active=True,
            member_count=10
        )
        self.community_inactive = Community.objects.create(
            name='secret_club',
            slug='secret_club',
            description='A secret community.',
            creator=self.user1,
            is_active=False,
            member_count=5
        )

        # Create posts
        self.post_published = Post.objects.create(
            title='How to write Django tests',
            slug='how-to-write-django-tests',
            content='Testing in Django is easy and useful.',
            author=self.user1,
            community=self.community_active,
            is_deleted=False
        )
        self.post_deleted = Post.objects.create(
            title='Old deleted post about testing',
            slug='old-deleted-post-about-testing',
            content='This should not appear in search results.',
            author=self.user1,
            community=self.community_active,
            is_deleted=True
        )

    def test_search_results_posts(self):
        # Test searching for posts by title/content
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testing', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'How to write Django tests')
        self.assertNotContains(response, 'Old deleted post about testing')

        # Test authenticated post search with user votes prefetch
        self.client.login(username='bob_builder', password='password123')
        PostVote.objects.create(user=self.user2, post=self.post_published, value=1)

        response = self.client.get(url, {'q': 'testing', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        # Search active community
        response = self.client.get(url, {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/django_dev')

        # Search inactive community
        response = self.client.get(url, {'q': 'secret', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'c/secret_club')

    def test_search_results_users(self):
        url = reverse('search:results')
        # Search for a user
        response = self.client.get(url, {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/alice_wonder')
        self.assertNotContains(response, 'u/bob_builder')

    def test_search_suggestions_empty(self):
        url = reverse('search:suggestions')
        # Short query (< 2 characters)
        response = self.client.get(url, {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context.get('suggestions', [])), 0)

    def test_search_suggestions_valid(self):
        url = reverse('search:suggestions')
        # Query with length >= 2
        response = self.client.get(url, {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)  # Should find community and post

        # Check fields of suggestion items
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])
