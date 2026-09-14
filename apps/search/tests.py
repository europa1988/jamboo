from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='TestCommunity',
            slug='testcommunity',
            description='A test community description',
            creator=self.user,
            member_count=5
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Test post content here',
            author=self.user,
            community=self.community
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results') + '?q=a')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Запрос должен содержать минимум 2 символа')

    def test_search_results_posts_found(self):
        response = self.client.get(reverse('search:results') + '?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities_found(self):
        response = self.client.get(reverse('search:results') + '?q=TestCommunity&type=communities')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users_found(self):
        response = self.client.get(reverse('search:results') + '?q=testuser&type=users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions') + '?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
