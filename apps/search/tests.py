from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Create another test user (author)
        self.author = User.objects.create_user(username='authoruser', password='password123')

        # Create a test community
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Test community description',
            creator=self.user
        )

        # Create 15 posts to test pagination (10 per page limit)
        self.posts = []
        for i in range(15):
            post = Post.objects.create(
                title=f'Post Title {i:02d}',
                slug=f'post-title-{i}',
                content=f'Content of post {i} matching_keyword',
                community=self.community,
                author=self.author
            )
            self.posts.append(post)

        # Add a vote to the last post (newest, so on page 1 of -created_at) to test user_vote precalculation
        self.vote = PostVote.objects.create(
            user=self.user,
            post=self.posts[-1],
            value=1
        )

    def test_search_results_status_and_pagination(self):
        """
        Verify search_results view returns 200 OK and paginates with 10 results per page.
        """
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'matching_keyword', 'type': 'posts'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')

        # 15 matches should exist. Under pagination of 10, the first page should have exactly 10 posts.
        results = response.context['results']
        self.assertEqual(len(results), 10)
        self.assertEqual(response.context['total_count'], 15)

        # Page 2 should have exactly 5 posts
        response_page2 = self.client.get(url, {'q': 'matching_keyword', 'type': 'posts', 'page': 2})
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context['results']), 5)

    def test_search_results_authenticated_user_vote(self):
        """
        Verify that search_results sets post.user_vote correctly for authenticated users.
        """
        self.client.login(username='testuser', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'matching_keyword', 'type': 'posts'})

        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])

        # Find the post we voted for
        voted_post = next(p for p in results if p.id == self.posts[-1].id)
        self.assertEqual(voted_post.user_vote, 1)

    def test_search_results_invalid_or_short_query(self):
        """
        Verify that searching with short query returns an error message.
        """
        url = reverse('search:results')

        # Empty query
        response_empty = self.client.get(url, {'q': ''})
        self.assertEqual(response_empty.status_code, 200)
        self.assertIn('error', response_empty.context)
        self.assertEqual(response_empty.context['error'], "Введите поисковый запрос")

        # Short query
        response_short = self.client.get(url, {'q': 'a'})
        self.assertEqual(response_short.status_code, 200)
        self.assertIn('error', response_short.context)
        self.assertEqual(response_short.context['error'], "Поисковый запрос должен содержать не менее 2 символов")

    def test_search_suggestions_format(self):
        """
        Verify that search_suggestions returns expected dictionary keys ('url', 'type', 'title', 'subtitle').
        """
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Post Title'})

        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']

        # We should get suggestions list
        self.assertIsInstance(suggestions, list)
        self.assertTrue(len(suggestions) > 0)

        # Each suggestion must have 'url', 'type', 'title', and 'subtitle' keys
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)

            # Type must be one of post, community, or user
            self.assertIn(item['type'], ['post', 'community', 'user'])

    def test_search_suggestions_empty_for_short_query(self):
        """
        Verify that suggestions list is empty if the query is too short.
        """
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
