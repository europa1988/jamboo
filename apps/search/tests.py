from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='john_doe', password='password123')
        self.user2 = User.objects.create_user(username='jane_smith', password='password123')

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python discussion community',
            creator=self.user1,
            member_count=100
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django framework community',
            creator=self.user2,
            member_count=50
        )

        self.post1 = Post.objects.create(
            title='Learning Python basics',
            slug='learning-python-basics',
            content='Python is awesome and easy to learn.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Building web apps with Django',
            slug='building-web-apps-with-django',
            content='Django makes web development fast and clean.',
            author=self.user2,
            community=self.community2
        )

        # Vote and Follow setup
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_posts_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)
        self.assertIsNone(results[0].user_vote)

    def test_search_results_posts_authenticated(self):
        self.client.login(username='john_doe', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community2)

    def test_search_results_users_authenticated(self):
        self.client.login(username='john_doe', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'jane', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)
        self.assertTrue(results[0].is_following)

    def test_search_suggestions_endpoint(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))
