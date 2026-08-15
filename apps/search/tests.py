from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=100)
        self.user2 = User.objects.create_user(username='testuser2', password='password123', karma=50)

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming community',
            creator=self.user1,
            member_count=20
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django web framework community',
            creator=self.user2,
            member_count=10
        )

        self.post1 = Post.objects.create(
            title='Python 3.12 release features',
            slug='python-312-release-features',
            content='Awesome new features in Python 3.12',
            author=self.user1,
            community=self.community1,
            score=5
        )
        self.post2 = Post.objects.create(
            title='Django 6.0 tutorial for beginners',
            slug='django-60-tutorial-for-beginners',
            content='Learn how to build web apps with Django',
            author=self.user2,
            community=self.community2,
            score=3
        )

        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос.')

    def test_search_results_posts_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)
        self.assertIsNone(results[0].user_vote)

    def test_search_results_posts_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'community', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)

    def test_search_results_users_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)
        results = list(response.context['results'])
        u2 = [u for u in results if u.username == 'testuser2'][0]
        self.assertTrue(u2.is_following)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_matches(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))
