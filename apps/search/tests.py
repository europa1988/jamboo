from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(
            name='Python Community',
            slug='python',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Python Programming',
            content='Content about Python',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertGreater(len(response.context['suggestions']), 0)
