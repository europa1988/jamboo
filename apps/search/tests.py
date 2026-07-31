from django.test import TestCase, RequestFactory
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.search.views import search_results, search_suggestions
from django.db.models.query import QuerySet


class SearchTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='alice', email='alice@example.com', password='password')
        self.user2 = User.objects.create_user(username='bob', email='bob@example.com', password='password')
        self.user3 = User.objects.create_user(username='charlie', email='charlie@example.com', password='password')

        # Create user follow
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Create communities
        self.comm1 = Community.objects.create(
            name='python',
            slug='python',
            description='Django and Python related topics',
            creator=self.user1
        )
        self.comm2 = Community.objects.create(
            name='gaming',
            slug='gaming',
            description='All about games',
            creator=self.user2
        )

        # Create 12 posts to verify pagination (10 items per page limit)
        self.posts = []
        for i in range(12):
            post = Post.objects.create(
                title=f'Learn Django part {i}',
                slug=f'learn-django-{i}',
                content=f'This is a tutorial on Django part {i}',
                author=self.user1,
                community=self.comm1
            )
            self.posts.append(post)

        # Create post votes
        self.vote1 = PostVote.objects.create(user=self.user1, post=self.posts[0], value=1)
        self.vote2 = PostVote.objects.create(user=self.user1, post=self.posts[1], value=-1)

    def test_search_results_pagination(self):
        """Verify that search_results paginates results to 10 per page."""
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        total_count = response.context['total_count']

        self.assertEqual(total_count, 12)
        self.assertEqual(len(results), 10)  # Paginated to 10 items
        self.assertTrue(results.has_next())

    def test_search_results_prefetch_votes_authenticated(self):
        """Verify that search_results utilizes Prefetch for PostVote and populates user_vote correctly."""
        self.client.login(username='alice', password='password')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']

        # Check that user_vote was set correctly without extra N+1 queries
        for post in results:
            if post.id == self.posts[0].id:
                self.assertEqual(post.user_vote, 1)
                self.assertTrue(hasattr(post, 'prefetched_votes'))
            elif post.id == self.posts[1].id:
                self.assertEqual(post.user_vote, -1)
                self.assertTrue(hasattr(post, 'prefetched_votes'))
            else:
                self.assertIsNone(post.user_vote)

    def test_search_results_unauthenticated(self):
        """Verify search_results handles unauthenticated users properly."""
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        for post in results:
            self.assertFalse(hasattr(post, 'prefetched_votes'))
            self.assertIsNone(getattr(post, 'user_vote', None))

    def test_search_communities(self):
        """Verify searching for communities."""
        response = self.client.get(reverse('search:results'), {'q': 'py', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'python')

    def test_search_users_and_follow_flag(self):
        """Verify search_results for users and that the is_following flag is set correctly."""
        self.client.login(username='alice', password='password')
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        self.assertEqual(len(results), 1)
        profile_user = results[0]
        self.assertEqual(profile_user.username, 'bob')
        self.assertTrue(profile_user.is_following)  # alice is following bob

        # Search for Charlie (not followed)
        response2 = self.client.get(reverse('search:results'), {'q': 'charlie', 'type': 'users'})
        self.assertEqual(response2.status_code, 200)
        results2 = response2.context['results']
        self.assertEqual(len(results2), 1)
        profile_user2 = results2[0]
        self.assertEqual(profile_user2.username, 'charlie')
        self.assertFalse(profile_user2.is_following)

    def test_search_suggestions_contains_required_keys(self):
        """Verify that search_suggestions contains expected list of dicts with correct keys."""
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)

        suggestions = response.context['suggestions']
        query = response.context['query']

        self.assertEqual(query, 'py')
        self.assertGreater(len(suggestions), 0)

        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])

    def test_search_suggestions_empty_query(self):
        """Verify that short query returns empty suggestions list."""
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
