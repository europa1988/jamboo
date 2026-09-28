from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='Password123!', karma=10)
        self.user2 = User.objects.create_user(username='testuser2', password='Password123!', karma=5)

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='Python Tutorial',
            content='Learn python programming from scratch.',
            author=self.user1,
            community=self.community
        )

        self.post2 = Post.objects.create(
            title='Django Guide',
            content='Building apps with python and django.',
            author=self.user2,
            community=self.community
        )

    def test_search_results_posts_default(self):
        url = reverse('search:results') + '?q=python'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = list(response.context['results'])
        self.assertEqual(len(results), 2)
        self.assertEqual(response.context['search_type'], 'posts')

    def test_search_results_communities(self):
        url = reverse('search:results') + '?q=python&type=communities'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'python')

    def test_search_results_users(self):
        url = reverse('search:results') + '?q=testuser&type=users'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 2)

    def test_search_results_authenticated_with_votes_and_follows(self):
        self.client.force_login(self.user1)
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Test post user_vote attribute
        response = self.client.get(reverse('search:results') + '?q=Python&type=posts')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        post1_res = next(p for p in results if p.id == self.post1.id)
        self.assertEqual(post1_res.user_vote, 1)

        # Test user is_following attribute
        response = self.client.get(reverse('search:results') + '?q=testuser2&type=users')
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        user2_res = next(u for u in results if u.id == self.user2.id)
        self.assertTrue(user2_res.is_following)

    def test_search_suggestions_empty_for_short_query(self):
        url = reverse('search:suggestions') + '?q=a'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_returns_items(self):
        url = reverse('search:suggestions') + '?q=python'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        for item in suggestions:
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn('url', item)
