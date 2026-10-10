from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1,
            member_count=10
        )

        self.post1 = Post.objects.create(
            title='Django 6 Release Notes',
            slug='django-6-release-notes',
            content='Awesome features',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 Tips',
            slug='python-312-tips',
            content='Useful tricks',
            author=self.user2,
            community=self.community
        )

        PostVote.objects.create(
            user=self.user1,
            post=self.post1,
            value=PostVote.UPVOTE
        )

        UserFollow.objects.create(
            follower=self.user1,
            following=self.user2
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пожалуйста, введите поисковый запрос.')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.post1)

    def test_search_results_posts_authenticated_vote(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        post_in_ctx = response.context['results'][0]
        self.assertEqual(getattr(post_in_ctx, 'user_vote', None), PostVote.UPVOTE)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        user_in_ctx = response.context['results'][0]
        self.assertEqual(user_in_ctx, self.user2)
        self.assertTrue(getattr(user_in_ctx, 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
