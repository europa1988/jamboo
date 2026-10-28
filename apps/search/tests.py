from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='anotheruser', password='password123')

        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='A test community',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='Django testing post',
            slug='django-testing-post',
            content='Content for testing',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Another Django post',
            slug='another-django-post',
            content='More content',
            author=self.user2,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 2)

    def test_search_results_posts_authenticated_vote(self):
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testing', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testcomm', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'another', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = response.context['results']
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_following)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_valid_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [item['type'] for item in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
        self.assertIn('user', types)
