from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=5)
        self.user3 = User.objects.create_user(username='charlie', password='password123', karma=20)

        # Создаем сообщества
        self.community1 = Community.objects.create(
            name='django',
            slug='django',
            description='Django Web Framework community',
            creator=self.user1,
            member_count=100
        )
        self.community2 = Community.objects.create(
            name='python',
            slug='python',
            description='General Python programming community',
            creator=self.user2,
            member_count=200
        )

        # Создаем посты
        self.post1 = Post.objects.create(
            title='Getting Started with Django',
            slug='getting-started-with-django',
            content='This is a tutorial on Django framework.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Python Tips and Tricks',
            slug='python-tips-and-tricks',
            content='Some cool python syntax features.',
            author=self.user2,
            community=self.community2
        )

        # Добавим голоса
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        PostVote.objects.create(user=self.user1, post=self.post2, value=-1)

        # Добавим подписки
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос')

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Поисковый запрос должен содержать не менее 2 символов')
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Поисковый запрос должен содержать не менее 2 символов')

    def test_search_results_posts_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)
        # Так как пользователь не аутентифицирован, user_vote должно быть None
        self.assertFalse(hasattr(results[0], 'user_vote') or results[0].get_user_vote(None) is not None)

    def test_search_results_posts_authenticated(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post2)
        # Проверяем precalculated user_vote
        self.assertEqual(results[0].user_vote, -1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'py', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community2)

    def test_search_results_users_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'bo', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)
        # Подписка должна быть False для неаутентифицированного
        self.assertFalse(results[0].is_following)

    def test_search_results_users_authenticated(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)
        # Для alice подписка на bob должна быть True
        self.assertTrue(results[0].is_following)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 1)

        # Проверим формат элементов в списке предложений
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])
