from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(
            name='testcommunity',
            slug='testcommunity',
            creator=self.user,
            description='A test community description'
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            content='Test Post Content',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'testcommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertTrue(len(response.context['suggestions']) >= 1)
