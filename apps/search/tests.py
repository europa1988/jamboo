from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='john_doe', password='password123')
        self.user2 = User.objects.create_user(username='jane_smith', password='password123')

        self.community = Community.objects.create(
            name='python_devs',
            slug='python_devs',
            description='Community for Python developers',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='Learn Django Step by Step',
            slug='learn-django-step-by-step',
            content='Django is an awesome framework.',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Mastering Python Asyncio',
            slug='mastering-python-asyncio',
            content='Asyncio is powerful.',
            author=self.user2,
            community=self.community
        )

        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_get_absolute_urls(self):
        self.assertEqual(self.user1.get_absolute_url(), reverse('users:profile', kwargs={'username': 'john_doe'}))
        self.assertEqual(self.community.get_absolute_url(), reverse('communities:detail', kwargs={'slug': 'python_devs'}))

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertIsNotNone(response.context['error'])

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['error'])
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post1)

    def test_search_results_posts_authenticated_vote(self):
        self.client.login(username='john_doe', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        post = response.context['results'][0]
        self.assertEqual(post.user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['error'])
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        self.client.login(username='john_doe', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'jane', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['error'])
        self.assertEqual(response.context['total_count'], 1)
        u = response.context['results'][0]
        self.assertEqual(u, self.user2)
        self.assertTrue(getattr(u, 'is_following', False))

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'j'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
