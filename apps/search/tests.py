from django.test import TestCase, RequestFactory
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username="test_user_alice", email="alice@test.com", password="password123")
        self.user2 = User.objects.create_user(username="test_user_bob", email="bob@test.com", password="password123")

        # Create community
        self.community = Community.objects.create(
            name="testcommunity",
            slug="testcommunity",
            description="A community for testing",
            creator=self.user1
        )

        # Create posts
        self.post1 = Post.objects.create(
            title="Alice's first post",
            slug="alices-first-post",
            content="Hello world from Alice",
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title="Bob's awesome post",
            slug="bobs-awesome-post",
            content="Hello world from Bob",
            author=self.user2,
            community=self.community
        )

    def test_search_results_page_posts(self):
        # Test basic search on posts
        response = self.client.get(reverse('search:results'), {'q': 'Alice', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)

    def test_search_results_query_length_error(self):
        # Test short search query error
        response = self.client.get(reverse('search:results'), {'q': 'a', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Длина запроса должна быть не менее 2 символов")

    def test_search_results_users_ordering(self):
        # Test user search with explicit ordering
        response = self.client.get(reverse('search:results'), {'q': 'test_user', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        # Results should contain Alice and Bob ordered alphabetically
        results_usernames = [u.username for u in response.context['results']]
        self.assertEqual(results_usernames, ["test_user_alice", "test_user_bob"])

    def test_search_suggestions_htmx(self):
        # Test HTMX suggestions
        response = self.client.get(reverse('search:suggestions'), {'q': 'Alice'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        # Check suggestion item values
        suggestions = response.context['suggestions']
        self.assertTrue(any(item['type'] == 'post' and "Alice" in item['title'] for item in suggestions))
