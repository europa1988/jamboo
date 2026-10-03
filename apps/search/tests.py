from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='Password123!'
        )
        self.other_user = User.objects.create_user(
            username='searchguy',
            password='Password123!'
        )
        self.community = Community.objects.create(
            name='pythoncommunity',
            slug='pythoncommunity',
            description='A community for Python lovers.',
            creator=self.user,
            member_count=5
        )
        self.post = Post.objects.create(
            title='Python 3.12 released with great features',
            slug='python-312-released',
            content='Full content about Python 3.12 release.',
            author=self.user,
            community=self.community
        )
        PostVote.objects.create(
            user=self.user,
            post=self.post,
            value=PostVote.UPVOTE
        )

    def test_search_results_posts_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.post)
        self.assertIsNone(response.context['results'][0].user_vote)

    def test_search_results_posts_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0].user_vote, PostVote.UPVOTE)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user, following=self.other_user)
        self.client.force_login(self.user)
        response = self.client.get(reverse('search:results'), {'q': 'search', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        searched_user = response.context['results'][0]
        self.assertEqual(searched_user, self.other_user)
        self.assertTrue(getattr(searched_user, 'is_following', False))

    def test_search_results_short_query_error(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
