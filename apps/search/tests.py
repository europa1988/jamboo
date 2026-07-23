from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchTests(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=100)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=50)

        # Создаем сообщество
        self.community1 = Community.objects.create(
            name='django',
            slug='django',
            description='Django framework community',
            creator=self.user1,
            member_count=10
        )
        self.community2 = Community.objects.create(
            name='python',
            slug='python',
            description='Python general community',
            creator=self.user1,
            member_count=5
        )

        # Создаем посты
        self.post1 = Post.objects.create(
            title='Learn Django today',
            slug='learn-django-today',
            content='This is a tutorial on Django views and models.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Python patterns',
            slug='python-patterns',
            content='Advanced design patterns in Python.',
            author=self.user2,
            community=self.community2
        )

        # Настраиваем подписку (alice -> bob)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Настраиваем голос bob за post1 (bob upvoted post1)
        PostVote.objects.create(user=self.user2, post=self.post1, value=1)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_too_short_query(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Запрос слишком короткий')

    def test_search_results_posts_type(self):
        # Ищем посты со словом 'Django'
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertTemplateUsed(response, 'search/partials/post_results.html')

        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)

        # Так как гость, user_vote должен быть None
        self.assertIsNone(results[0].user_vote)

    def test_search_results_posts_authenticated_user_vote(self):
        # Логиним bob
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        self.assertEqual(len(results), 1)
        # Проверяем, что голос bob подгрузился как 1
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities_type(self):
        # Ищем сообщества со словом 'django'
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/community_results.html')

        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community1)

    def test_search_results_users_type_guest(self):
        # Ищем пользователей со словом 'bob' в гостевом режиме
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/user_results.html')

        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)
        # Гость, поэтому is_following = False
        self.assertFalse(results[0].is_following)

    def test_search_results_users_type_authenticated_following(self):
        # Логиним alice (подписана на bob)
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)
        # Так как alice подписана на bob, is_following должно быть True
        self.assertTrue(results[0].is_following)

    def test_search_suggestions_empty_query(self):
        response = self.client.get(reverse('search:suggestions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        # Ищем suggestions для 'py' (найдет пост python-patterns, сообщество python, возможно пользователей, если бы в имени было py)
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')

        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 2)

        # Проверяем структуру предложений
        types = [item['type'] for item in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
