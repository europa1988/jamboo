from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming community',
            creator=self.user,
            member_count=5
        )
        self.post = Post.objects.create(
            title='Django Search Tutorial',
            slug='django-search-tutorial',
            content='How to implement search in Django',
            author=self.user,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
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
        response = self.client.get(url, {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user)

    def test_search_results_authenticated_vote_prefetch(self):
        PostVote.objects.create(user=self.user, post=self.post, value=PostVote.UPVOTE)
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = response.context['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, PostVote.UPVOTE)

    def test_search_results_pagination(self):
        for i in range(15):
            Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                content='Pagination content test',
                author=self.user,
                community=self.community
            )
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Pagination', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 10)
        self.assertEqual(response.context['total_count'], 15)

    def test_search_suggestions_empty_or_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        self.assertEqual(response.context['suggestions'], [])

    def test_search_suggestions_matching_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 1)
        item = suggestions[0]
        self.assertIn('url', item)
        self.assertIn('type', item)
        self.assertIn('title', item)
        self.assertIn('subtitle', item)
        self.assertEqual(item['type'], 'post')
        self.assertEqual(item['title'], 'Django Search Tutorial')
