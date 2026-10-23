from django.test import TestCase
from django.urls import reverse

from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='searchuser',
            email='search@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='pythondev',
            slug='pythondev',
            description='Python discussion community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Python 3.12 release notes',
            content='Detailed notes on Python 3.12 features',
            author=self.user,
            community=self.community
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_posts_type(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_communities_type(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users_type_authenticated(self):
        UserFollow.objects.create(follower=self.user, following=self.other_user)
        self.client.force_login(self.user)

        response = self.client.get(reverse('search:results'), {'q': 'other', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)

        found_user = response.context['results'][0]
        self.assertEqual(found_user, self.other_user)
        self.assertTrue(getattr(found_user, 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'post' for s in suggestions))
        self.assertTrue(any(s['type'] == 'community' for s in suggestions))

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
