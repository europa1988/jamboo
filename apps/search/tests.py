from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='anotheruser', password='password123', karma=25)

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python community discussion',
            creator=self.user1,
            member_count=100
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django web framework group',
            creator=self.user2,
            member_count=50
        )

        self.post1 = Post.objects.create(
            title='Learning Python Basics',
            slug='learning-python-basics',
            content='Python is awesome and versatile.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Building Web Apps with Django',
            slug='building-web-apps-with-django',
            content='Django makes web development fast and easy.',
            author=self.user2,
            community=self.community2
        )

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос.')

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post1, response.context['results'])

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'web', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community2, response.context['results'])

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.user1, response.context['results'])

    def test_search_results_authenticated_user_following(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='testuser1', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'anotheruser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        user_in_results = list(response.context['results'])[0]
        self.assertTrue(user_in_results.is_following)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
