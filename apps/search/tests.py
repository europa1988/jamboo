from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow, UserProfile
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        # Создаем профиль для пользователей, если они не создаются автоматически сигналами
        UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.get_or_create(user=self.user2)

        # Создаем сообщество
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Сообщество о веб-фреймворке Django',
            creator=self.user1
        )

        # Создаем посты
        self.post1 = Post.objects.create(
            title='Изучаем Django с нуля',
            slug='learn-django',
            content='Django это круто',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Релиз Django 6.0',
            slug='django-6-release',
            content='Множество новых фич',
            author=self.user2,
            community=self.community
        )

    def test_search_results_empty_query(self):
        """Проверяем ошибку при пустом запросе."""
        response = self.client.get(reverse('search:results'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос.')

    def test_search_results_short_query(self):
        """Проверяем ошибку при слишком коротком запросе."""
        response = self.client.get(reverse('search:results'), {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Запрос должен быть не менее 2 символов.')

    def test_search_results_posts_pagination(self):
        """Проверяем пагинацию по 10 постов на страницу."""
        # Создаем еще 10 постов с ключевым словом Django в заголовке (всего станет 12)
        for i in range(10):
            Post.objects.create(
                title=f'Пост про Django {i}',
                slug=f'django-post-{i}',
                content='Контент',
                author=self.user1,
                community=self.community
            )

        # Первая страница
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 12)
        self.assertEqual(len(response.context['results']), 10)
        self.assertTrue(response.context['results'].has_next())

        # Вторая страница
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts', 'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 2)
        self.assertFalse(response.context['results'].has_next())

    def test_search_results_posts_prefetch_votes(self):
        """Проверяем префетчинг голосов для авторизованных пользователей."""
        # Голосуем за post1 от имени user1
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)

        # Неавторизованный пользователь
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        for post in results:
            self.assertIsNone(post.user_vote)

        # Авторизованный пользователь
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        # Находим post1 в результатах и проверяем его user_vote
        post1_found = False
        for post in results:
            if post.id == self.post1.id:
                self.assertEqual(post.user_vote, PostVote.UPVOTE)
                post1_found = True
            else:
                self.assertIsNone(post.user_vote)
        self.assertTrue(post1_found)

    def test_search_results_users_is_following(self):
        """Проверяем установку is_following для результатов поиска пользователей."""
        # Подписываем user1 на user2
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Авторизуемся под user1
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        self.assertEqual(len(results), 2)  # Должны найти testuser1 и testuser2

        for u in results:
            if u.id == self.user2.id:
                self.assertTrue(u.is_following)
            else:
                self.assertFalse(u.is_following)

    def test_search_suggestions_context_keys(self):
        """Проверяем, что search_suggestions возвращает корректную структуру данных в контексте."""
        # Ищем по запросу "django"
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)

        # Должны быть в состоянии прочитать контекст, так как использовался render()
        self.assertIn('suggestions', response.context)
        self.assertIn('query', response.context)
        self.assertEqual(response.context['query'], 'django')

        suggestions = response.context['suggestions']
        # Должно найти как минимум сообщество и посты
        self.assertTrue(len(suggestions) > 0)

        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])
