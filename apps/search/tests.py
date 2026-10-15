from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='A test community description',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='First Test Post',
            slug='first-test-post',
            content='This is python content',
            author=self.user1,
            community=self.community
        )

        self.post2 = Post.objects.create(
            title='Second Post Django',
            slug='second-post-django',
            content='More django content',
            author=self.user2,
            community=self.community
        )

    def test_search_results_short_query(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0].id, self.post1.id)

    def test_search_results_posts_authenticated_vote(self):
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results'][0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0].id, self.community.id)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser2', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        user_result = response.context['results'][0]
        self.assertEqual(user_result.id, self.user2.id)
        self.assertTrue(user_result.is_following)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))
        self.assertTrue(any(s['type'] == 'user' for s in suggestions))
