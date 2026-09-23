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
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='anotheruser', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user,
            member_count=1
        )

        self.post = Post.objects.create(
            title='Django Search Feature',
            slug='django-search-feature',
            content='Testing search feature in Django',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'another', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.other_user)

    def test_search_results_pagination(self):
        for i in range(12):
            Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content='Test content',
                author=self.user,
                community=self.community
            )
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Test', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 10)
        self.assertTrue(response.context['results'].has_next())

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Djan'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 1)

        item = suggestions[0]
        self.assertIn('url', item)
        self.assertIn('type', item)
        self.assertIn('title', item)
        self.assertIn('subtitle', item)
        self.assertEqual(item['type'], 'post')

    def test_search_authenticated_user_votes_and_follows(self):
        PostVote.objects.create(user=self.user, post=self.post, value=1)
        UserFollow.objects.create(follower=self.user, following=self.other_user)
        self.client.force_login(self.user)

        # Test post user_vote
        url = reverse('search:results')
        res_post = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(res_post.context['results'][0].user_vote, 1)

        # Test user is_following
        res_user = self.client.get(url, {'q': 'another', 'type': 'users'})
        self.assertEqual(res_user.status_code, 200)
        self.assertTrue(res_user.context['results'][0].is_following)
