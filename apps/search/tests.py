from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='alice', email='alice@example.com', password='password')
        self.user2 = User.objects.create_user(username='bob', email='bob@example.com', password='password')

        # Create community
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Django community',
            creator=self.user1
        )

        # Create post
        self.post = Post.objects.create(
            title='Learning Django 6',
            slug='learning-django-6',
            content='This is a tutorial on Django 6.',
            author=self.user1,
            community=self.community
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Learning Django 6')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/django')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/alice')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        # Suggestions return HTML list. Let's make sure it contains the items.
        self.assertContains(response, 'Learning Django 6')
        self.assertContains(response, 'c/django')
