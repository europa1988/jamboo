from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=100)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=50)

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1,
            member_count=10
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django community',
            creator=self.user2,
            member_count=5
        )

        self.post1 = Post.objects.create(
            title='Learning Python Basics',
            slug='learning-python-basics',
            content='Python is awesome',
            author=self.user1,
            community=self.community1,
            score=10
        )
        self.post2 = Post.objects.create(
            title='Django Web Development',
            slug='django-web-development',
            content='Django is full-featured',
            author=self.user2,
            community=self.community2,
            score=15
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.post1.id)

    def test_search_results_posts_authenticated_vote_precalculated(self):
        self.client.login(username='alice', password='password123')
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)

        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.community2.id)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.user1.id)

    def test_search_results_users_authenticated_follow_precalculated(self):
        self.client.login(username='alice', password='password123')
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertTrue(getattr(results[0], 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        titles = [s['title'] for s in suggestions]
        self.assertIn('Learning Python Basics', titles)
        self.assertIn('c/python', titles)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'P'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
