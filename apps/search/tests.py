from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем пользователей
        self.user = User.objects.create_user(
            username='search_user_test',
            email='test@example.com',
            password='password123',
            karma=150
        )
        self.another_user = User.objects.create_user(
            username='another_guy',
            email='another@example.com',
            password='password123'
        )

        # Создаем сообщество
        self.community = Community.objects.create(
            name='TestCommunity',
            slug='test-community',
            description='This is a test community for search purposes',
            creator=self.user,
            member_count=42
        )

        # Создаем пост
        self.post = Post.objects.create(
            title='Super Awesome Post about Django',
            slug='super-awesome-post',
            content='This is some random test content about Python and Django search features.',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts_by_title(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Awesome Post')
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(len(response.context['results']), 1)

    def test_search_results_posts_by_content(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Awesome Post')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'TestCommunity', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/TestCommunity')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'search_user', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/search_user_test')
        self.assertEqual(response.context['total_count'], 1)

    def test_search_suggestions_endpoint(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в контексте suggestions имеет правильные ключи
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)

        # Каждый элемент предложения должен содержать url, type, title, subtitle
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)

            if item['type'] == 'post':
                self.assertEqual(item['title'], self.post.title)
                self.assertIn('c/TestCommunity', item['subtitle'])
                self.assertIn('u/search_user_test', item['subtitle'])

    def test_search_results_authenticated_prefetch(self):
        # Апвоутим пост от лица another_user
        PostVote.objects.create(
            user=self.another_user,
            post=self.post,
            value=PostVote.UPVOTE
        )

        # Авторизуем another_user в клиенте
        self.client.login(username='another_guy', password='password123')

        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        # Проверяем, что user_vote проставился из Prefetch
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.user_vote, PostVote.UPVOTE)
