from django.test import TestCase, RequestFactory
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
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='anotheruser', password='password123', karma=5)

        # Create a community
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='A community about Django framework',
            creator=self.user1,
            is_active=True
        )

        self.inactive_community = Community.objects.create(
            name='inactive_comm',
            slug='inactive_comm',
            description='Inactive community description',
            creator=self.user1,
            is_active=False
        )

        # Create posts
        self.post1 = Post.objects.create(
            title='Learn Django is fun',
            slug='learn-django',
            content='Django is an awesome python framework.',
            author=self.user1,
            community=self.community,
            is_deleted=False
        )

        self.post2 = Post.objects.create(
            title='Flask tutorial',
            slug='flask-tutorial',
            content='Flask is also nice but Django is more complete.',
            author=self.user2,
            community=self.community,
            is_deleted=False
        )

        self.deleted_post = Post.objects.create(
            title='Deleted Django Post',
            slug='deleted-django',
            content='This post has been deleted.',
            author=self.user1,
            community=self.community,
            is_deleted=True
        )

    def test_search_results_no_query(self):
        """If there is no query parameter, return empty results."""
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertIsNone(response.context['results'])
        self.assertEqual(response.context['total_count'], 0)

    def test_search_results_short_query(self):
        """If query is less than 2 characters, show an error."""
        response = self.client.get(reverse('search:results') + '?q=a')
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос (минимум 2 символа)')

    def test_search_posts(self):
        """Search posts by title or content."""
        response = self.client.get(reverse('search:results') + '?q=Django&type=posts')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        # Matches post1 (title) and post2 (content), but not deleted_post
        self.assertEqual(len(results), 2)
        self.assertIn(self.post1, results)
        self.assertIn(self.post2, results)
        self.assertNotIn(self.deleted_post, results)

    def test_search_communities(self):
        """Search communities by name or description."""
        response = self.client.get(reverse('search:results') + '?q=django&type=communities')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertIn(self.community, results)
        self.assertNotIn(self.inactive_community, results)

    def test_search_users(self):
        """Search users by username."""
        response = self.client.get(reverse('search:results') + '?q=testuser&type=users')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertIn(self.user1, results)

    def test_search_suggestions(self):
        """Search suggestions should provide items for posts, communities, and users."""
        response = self.client.get(reverse('search:suggestions') + '?q=django')
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        # suggestions should be a list of dicts with the required keys
        self.assertTrue(len(suggestions) > 0)
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])

    def test_search_results_post_votes_prefetch(self):
        """Ensure post votes are prefetched and user_vote attribute is set for logged in user."""
        self.client.login(username='testuser1', password='password123')

        # Create a vote
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)

        response = self.client.get(reverse('search:results') + '?q=Django&type=posts')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])

        # Check that post1.user_vote is 1, and post2.user_vote is None
        p1 = [p for p in results if p.id == self.post1.id][0]
        p2 = [p for p in results if p.id == self.post2.id][0]
        self.assertEqual(p1.user_vote, 1)
        self.assertIsNone(p2.user_vote)

    def test_search_results_user_following(self):
        """Ensure is_following attribute is set correctly for users."""
        self.client.login(username='testuser1', password='password123')

        # Create following relation
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        response = self.client.get(reverse('search:results') + '?q=user&type=users')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])

        u2 = [u for u in results if u.id == self.user2.id][0]
        self.assertTrue(u2.is_following)
