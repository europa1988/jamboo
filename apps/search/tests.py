from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='john_doe', password='password123', karma=20)

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python discussion group',
            creator=self.user1,
            member_count=5
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django framework channel',
            creator=self.user1,
            member_count=10
        )

        self.post1 = Post.objects.create(
            title='Learn Python Basics',
            slug='learn-python-basics',
            content='Python tutorial for beginners',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Django Web Development',
            slug='django-web-development',
            content='Building web apps with Django',
            author=self.user2,
            community=self.community2
        )

        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос (минимум 2 символа).')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(list(response.context['results']), [self.post1])

    def test_search_results_posts_authenticated_vote(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(list(response.context['results']), [self.community2])

    def test_search_results_users(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'john', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        users = list(response.context['results'])
        self.assertEqual(users[0], self.user2)
        self.assertTrue(getattr(users[0], 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
