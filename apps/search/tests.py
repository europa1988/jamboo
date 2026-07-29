from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community, CommunityMember
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

        # Создаем пользователей
        self.user1 = self.User.objects.create_user(
            username='search_user_one',
            email='user1@example.com',
            password='password123',
            karma=10
        )
        self.user2 = self.User.objects.create_user(
            username='other_guy',
            email='user2@example.com',
            password='password123',
            karma=5
        )

        # Создаем сообщество
        self.community = Community.objects.create(
            name='TestSearchCommunity',
            slug='test-search-community',
            description='Community for testing search functionality.',
            creator=self.user1,
            member_count=1
        )
        CommunityMember.objects.create(
            user=self.user1,
            community=self.community,
            role='admin'
        )

        # Создаем посты
        self.post1 = Post.objects.create(
            title='Django search optimization tips',
            slug='django-search-optimization-tips',
            content='This is a test post about search queries.',
            author=self.user1,
            community=self.community,
            post_type='text'
        )
        self.post2 = Post.objects.create(
            title='How to write tests in Django',
            slug='how-to-write-tests-in-django',
            content='Testing makes your search app reliable.',
            author=self.user2,
            community=self.community,
            post_type='text'
        )

    def test_search_suggestions_by_query_string(self):
        """Проверяем автодополнение (HTMX) по ключевым словам."""
        url = reverse('search:suggestions')

        # Ищем постов по теме 'Django'
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django search optimization tips')
        self.assertContains(response, 'How to write tests in Django')

        # Ищем сообщество
        response = self.client.get(url, {'q': 'TestSearch'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/TestSearchCommunity')

        # Ищем пользователя
        response = self.client.get(url, {'q': 'search_user'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/search_user_one')

    def test_search_results_posts_tab(self):
        """Проверяем полноценный поиск постов."""
        url = reverse('search:results')

        # Поиск постов без логина
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django search optimization tips')
        self.assertContains(response, 'How to write tests in Django')

        # Логинимся и проверяем, что голоса подгружаются корректно
        self.client.login(username='search_user_one', password='password123')
        # Создаем голос за пост
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)

        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        # Проверяем, что кверисет постов содержит user_vote
        posts = response.context['results']
        post1_obj = next(p for p in posts if p.id == self.post1.id)
        self.assertEqual(post1_obj.user_vote, 1)

    def test_search_results_communities_tab(self):
        """Проверяем полноценный поиск сообществ."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'TestSearch', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/TestSearchCommunity')

    def test_search_results_users_tab(self):
        """Проверяем полноценный поиск пользователей."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'search_user', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/search_user_one')

    def test_search_results_empty_query(self):
        """Проверяем обработку пустого запроса."""
        url = reverse('search:results')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')
