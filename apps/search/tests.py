from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', karma=100)
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user,
            member_count=5
        )
        self.post = Post.objects.create(
            title='Django search test',
            content='This is a post about Django search',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], self.user)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['title'] == 'Django search test' for s in suggestions))
