from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.communities.models import Community
from apps.posts.models import Post

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='searchuser', password='password123')
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            description='Test community description',
            creator=self.user,
            is_active=True
        )
        self.post = Post.objects.create(
            title='Test Post Search Query',
            slug=slugify('Test Post Search Query'),
            content='Some content for search post',
            author=self.user,
            community=self.community
        )

    def test_search_results_view_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Search Query', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['results'])

    def test_search_results_view_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_view_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'searchuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, response.context['results'])

    def test_search_suggestions_view(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Search'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
