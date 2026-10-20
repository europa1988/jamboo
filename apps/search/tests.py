from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import UserFollow
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='anotheruser', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python discussion community',
            creator=self.user,
            member_count=10
        )

        self.post = Post.objects.create(
            title='Django 6.0 features',
            slug='django-60-features',
            content='Great new features in Django',
            author=self.user,
            community=self.community
        )

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(response.context['query'], '')
        self.assertEqual(response.context['total_count'], 0)

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'another', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.other_user, response.context['results'])

    def test_search_results_authenticated_user_vote_and_follow(self):
        self.client.login(username='testuser', password='password123')
        PostVote.objects.create(user=self.user, post=self.post, value=1)
        UserFollow.objects.create(follower=self.user, following=self.other_user)

        # Test post user_vote
        url = reverse('search:results')
        res_post = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        p = res_post.context['results'].object_list[0]
        self.assertEqual(p.user_vote, 1)

        # Test user is_following
        res_user = self.client.get(url, {'q': 'another', 'type': 'users'})
        u = res_user.context['results'].object_list[0]
        self.assertTrue(getattr(u, 'is_following', False))

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_valid_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))
