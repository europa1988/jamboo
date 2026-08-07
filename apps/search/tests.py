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
        # Create users
        self.user1 = User.objects.create_user(username='testuser1', password='password1', karma=10)
        self.user2 = User.objects.create_user(username='anotheruser', password='password1', karma=50)

        # Create user profile for anotheruser (some databases create this via signal, let's make sure it has bio)
        if hasattr(self.user2, 'profile'):
            self.user2.profile.bio = "Django Developer from Moscow"
            self.user2.profile.save()

        # Create communities
        self.community1 = Community.objects.create(
            name='django_devs',
            slug='django-devs',
            description='A community for Django developers.',
            creator=self.user1,
            member_count=100
        )
        self.community2 = Community.objects.create(
            name='python_devs',
            slug='python-devs',
            description='A community for Python lovers.',
            creator=self.user2,
            member_count=200
        )

        # Create posts
        self.post1 = Post.objects.create(
            title='Learning Django 6.x is awesome!',
            slug='learning-django-6x',
            content='Today we are learning how to build nice search systems in Django 6.',
            author=self.user2,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312-release',
            content='Check out the latest features in Python 3.12.',
            author=self.user1,
            community=self.community2
        )

    def test_search_results_posts(self):
        """Test searching for posts with pagination and context."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(response.context['query'], 'Django')
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post1)

    def test_search_results_posts_authenticated(self):
        """Test searching for posts for authenticated users with user_vote set."""
        # Create a vote for post1 by user1
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)

        self.client.login(username='testuser1', password='password1')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results'].object_list
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        """Test searching for communities ordered by member_count."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'devs', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')

        results = list(response.context['results'].object_list)
        self.assertEqual(len(results), 2)
        # Ordered by -member_count: python_devs (200) first, then django_devs (100)
        self.assertEqual(results[0], self.community2)
        self.assertEqual(results[1], self.community1)

    def test_search_results_users(self):
        """Test searching for users ordered by username."""
        # Follow anotheruser by testuser1
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        self.client.login(username='testuser1', password='password1')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'user', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')

        results = list(response.context['results'].object_list)
        self.assertEqual(len(results), 2)
        # Ordered by username: 'anotheruser' before 'testuser1'
        self.assertEqual(results[0], self.user2)
        self.assertTrue(results[0].is_following)
        self.assertEqual(results[1], self.user1)
        self.assertFalse(results[1].is_following)

    def test_search_suggestions(self):
        """Test autocomplete search suggestions endpoint."""
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')

        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)

        # Check suggestion item structure
        first_item = suggestions[0]
        self.assertIn('url', first_item)
        self.assertIn('type', first_item)
        self.assertIn('title', first_item)
        self.assertIn('subtitle', first_item)

        # Verify specific entries
        types = [item['type'] for item in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_empty_query(self):
        """Test searching with an empty query."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': '', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 0)
