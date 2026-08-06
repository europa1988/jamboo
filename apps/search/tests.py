from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user1 = User.objects.create_user(username='testuser1', password='password1')
        self.user2 = User.objects.create_user(username='alice', password='password1')

        # Create community
        self.community = Community.objects.create(
            name='programming',
            slug='programming',
            description='A community about coding',
            creator=self.user1
        )

        # Create posts
        self.posts = []
        for i in range(15):
            post = Post.objects.create(
                title=f'Django Tutorial Part {i}',
                slug=f'django-tutorial-part-{i}',
                content=f'This is a tutorial about Django, part {i}.',
                author=self.user1,
                community=self.community
            )
            self.posts.append(post)

        # Create a PostVote
        self.post_vote = PostVote.objects.create(
            user=self.user1,
            post=self.posts[14],
            value=1
        )

        # Create user follow
        self.follow = UserFollow.objects.create(
            follower=self.user1,
            following=self.user2
        )

    def test_search_results_posts_pagination(self):
        """
        Check that search_results view returns 10 items per page for posts and supports pagination.
        """
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 10)
        self.assertEqual(response.context['total_count'], 15)

        # Check second page
        response_page2 = self.client.get(url, {'q': 'Django', 'type': 'posts', 'page': 2})
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context['results']), 5)

    def test_search_results_user_vote_precalculated(self):
        """
        Check that search_results sets user_vote correctly on the posts for authenticated users.
        """
        self.client.login(username='testuser1', password='password1')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        # We need to find the specific post in the page results that has a vote
        results = response.context['results']
        voted_post = None
        for post in results:
            if post.id == self.posts[14].id:
                voted_post = post
                break

        self.assertIsNotNone(voted_post)
        self.assertEqual(voted_post.user_vote, 1)

    def test_search_results_users_is_following_precalculated(self):
        """
        Check that search_results sets is_following correctly for users search.
        """
        self.client.login(username='testuser1', password='password1')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'alice', 'type': 'users'})
        self.assertEqual(response.status_code, 200)

        results = response.context['results']
        self.assertEqual(len(results), 1)
        found_user = results[0]
        self.assertEqual(found_user.username, 'alice')
        self.assertTrue(found_user.is_following)

    def test_search_suggestions_response_keys(self):
        """
        Check that search_suggestions autocomplete returns dictionary items with 'url', 'type', 'title', and 'subtitle' keys.
        """
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'programming'})
        self.assertEqual(response.status_code, 200)

        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 1)
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertEqual(item['type'], 'community')
            self.assertIn('programming', item['title'])
