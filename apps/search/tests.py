from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='john_doe', password='password123', karma=50)

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming language community',
            creator=self.user1,
            member_count=100
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django web framework',
            creator=self.user2,
            member_count=50
        )

        self.post1 = Post.objects.create(
            title='Django for Beginners',
            slug='django-for-beginners',
            content='Great guide on learning Django.',
            author=self.user1,
            community=self.community2,
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312-release-notes',
            content='Awesome new features in Python.',
            author=self.user2,
            community=self.community1,
        )
        self.post_deleted = Post.objects.create(
            title='Deleted Django Post',
            slug='deleted-django-post',
            content='This post was deleted.',
            author=self.user1,
            community=self.community2,
            is_deleted=True
        )

        # Vote setup
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)

        # Follow setup
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос')

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results') + '?q=a')
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Запрос должен содержать не менее 2 символов')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results') + '?q=Django&type=posts')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        results = response.context['results'].object_list
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)

    def test_search_results_posts_authenticated_user_vote(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results') + '?q=Django&type=posts')
        self.assertEqual(response.status_code, 200)
        results = response.context['results'].object_list
        self.assertEqual(results[0].user_vote, PostVote.UPVOTE)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results') + '?q=python&type=communities')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        results = response.context['results'].object_list
        self.assertEqual(results[0], self.community1)

    def test_search_results_users(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results') + '?q=john&type=users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        results = response.context['results'].object_list
        self.assertEqual(results[0], self.user2)
        self.assertTrue(results[0].is_following)

    def test_search_suggestions_endpoint(self):
        response = self.client.get(reverse('search:suggestions') + '?q=Django')
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertIsInstance(suggestions, list)
        self.assertTrue(len(suggestions) > 0)

        # Check suggestion structure
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions') + '?q=d')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
