from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


class SearchTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testsearchuser', password='password123')
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test search post title',
            slug='test-search-post-title',
            content='Some post content for searching.',
            author=self.user,
            community=self.community
        )

    def test_search_results_page(self):
        """Проверка страницы результатов поиска."""
        response = self.client.get(reverse('search:results'), {'q': 'Test search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test search post title')

    def test_search_results_communities(self):
        """Проверка поиска сообществ."""
        response = self.client.get(reverse('search:results'), {'q': 'testcomm', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/testcomm')

    def test_search_results_users(self):
        """Проверка поиска пользователей."""
        response = self.client.get(reverse('search:results'), {'q': 'testsearch', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testsearchuser')

    def test_search_suggestions(self):
        """Проверка HTMX-предложений автокомплита."""
        response = self.client.get(reverse('search:suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test search post title')
        self.assertContains(response, 'c/testcomm')
        self.assertContains(response, 'u/testsearchuser')

    def test_search_empty_query(self):
        """Проверка пустого поискового запроса."""
        response = self.client.get(reverse('search:results'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')
