from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        # Create community
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Django developers community',
            creator=self.user1
        )

        # Create post
        self.post = Post.objects.create(
            title='Learning Django web framework',
            slug='learning-django',
            content='This is a tutorial on Django framework.',
            author=self.user1,
            community=self.community
        )

        # User Bob votes for the post
        self.vote = PostVote.objects.create(
            user=self.user2,
            post=self.post,
            value=PostVote.UPVOTE
        )

        # User Bob follows Alice
        self.follow = UserFollow.objects.create(
            follower=self.user2,
            following=self.user1
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Learning Django web framework')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_posts_authenticated(self):
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        # Verify post.user_vote was prefetched and correctly populated without hitting DB
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, PostVote.UPVOTE)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/django')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/alice')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users_following_precalculated(self):
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = list(response.context['results'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_following)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'), {'q': '', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 0)

    def test_search_suggestions_empty(self):
        # Suggestion requires query length >= 2
        response = self.client.get(reverse('search:suggestions'), {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Suggestions')
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_matching(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        # Suggestions should contain keys 'url', 'type', 'title', 'subtitle'
        suggestions = response.context['suggestions']
        self.assertTrue(any(item['type'] == 'post' for item in suggestions))
        self.assertTrue(any(item['type'] == 'community' for item in suggestions))
