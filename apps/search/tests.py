from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchTestCase(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='alex_coder',
            email='alex@example.com',
            password='testpassword123'
        )
        self.user2 = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='testpassword123'
        )

        # Создаем сообщество
        self.community1 = Community.objects.create(
            name='Python Developers',
            slug='python-devs',
            description='Сообщество программистов на Python',
            creator=self.user1
        )
        self.community2 = Community.objects.create(
            name='Django Web',
            slug='django-web',
            description='Фреймворк Django',
            creator=self.user2
        )

        # Создаем посты
        self.post1 = Post.objects.create(
            title='Learning Python Basics',
            slug='learning-python-basics',
            content='This post covers Python basics.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Django Advanced Search',
            slug='django-advanced-search',
            content='Implementing search features in Django app.',
            author=self.user2,
            community=self.community2
        )

    def test_search_results_posts_title_and_content(self):
        """Тестирует полностраничный поиск постов по заголовку и содержимому."""
        # Поиск по заголовку
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.post1.id)

        # Поиск по содержимому
        response = self.client.get(url, {'q': 'search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.post2.id)

    def test_search_results_posts_pagination(self):
        """Тестирует пагинацию (10 результатов на страницу)."""
        # Создаем еще 10 постов со словом 'Django'
        for i in range(10):
            Post.objects.create(
                title=f'Django Tip #{i}',
                slug=f'django-tip-{i}',
                content='Useful tip.',
                author=self.user2,
                community=self.community2
            )

        url = reverse('search:results')
        # Всего у нас 11 постов со словом 'Django' (post2 + 10 новых)
        response = self.client.get(url, {'q': 'Django', 'type': 'posts', 'page': 1})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 10)  # Первые 10 результатов

        response = self.client.get(url, {'q': 'Django', 'type': 'posts', 'page': 2})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)  # Оставшийся 1 результат

    def test_search_results_communities(self):
        """Тестирует полностраничный поиск сообществ."""
        url = reverse('search:results')

        # Поиск по названию
        response = self.client.get(url, {'q': 'Python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        communities = response.context['results']
        self.assertEqual(len(communities), 1)
        self.assertEqual(communities[0].id, self.community1.id)

        # Поиск по описанию
        response = self.client.get(url, {'q': 'Фреймворк', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        communities = response.context['results']
        self.assertEqual(len(communities), 1)
        self.assertEqual(communities[0].id, self.community2.id)

    def test_search_results_users_and_follow_status(self):
        """Тестирует полностраничный поиск пользователей и статус подписки."""
        url = reverse('search:results')

        # Без авторизации
        response = self.client.get(url, {'q': 'alex', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = response.context['results']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, self.user1.id)
        self.assertFalse(users[0].is_following)

        # С авторизацией, пользователь alex_coder (user1) подписан на john_doe (user2)
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)

        response = self.client.get(url, {'q': 'john', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = response.context['results']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, self.user2.id)
        self.assertTrue(users[0].is_following)

    def test_search_results_post_votes_prefetch(self):
        """Тестирует prefetch для голосов пользователя (user_vote)."""
        url = reverse('search:results')

        # Голосуем за пост от имени john_doe (user2)
        PostVote.objects.create(user=self.user2, post=self.post1, value=PostVote.UPVOTE)

        self.client.force_login(self.user2)
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, PostVote.UPVOTE)

    def test_search_suggestions_short_query(self):
        """Тестирует, что при запросе короче 2 символов подсказок нет."""
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_full(self):
        """Тестирует возвращаемые поисковые подсказки."""
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']

        # Должен найти post1 и community1
        self.assertGreaterEqual(len(suggestions), 2)

        # Проверяем структуру подсказки для поста
        post_suggestion = next(item for item in suggestions if item['type'] == 'post')
        self.assertEqual(post_suggestion['title'], self.post1.title)
        self.assertEqual(post_suggestion['url'], self.post1.get_absolute_url())
        self.assertIn('c/Python Developers', post_suggestion['subtitle'])

        # Проверяем структуру подсказки для сообщества
        community_suggestion = next(item for item in suggestions if item['type'] == 'community')
        self.assertEqual(community_suggestion['title'], 'c/Python Developers')
        self.assertIn('участников', community_suggestion['subtitle'])
