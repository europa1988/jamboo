from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='testuser2', password='password123', karma=20)
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1
        )
        self.post1 = Post.objects.create(
            title='Django Search Tutorial',
            content='How to build search in Django',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Python Tips and Tricks',
            content='Useful python code snippets',
            author=self.user2,
            community=self.community
        )

    def test_absolute_urls(self):
        self.assertEqual(self.user1.get_absolute_url(), reverse('users:profile', kwargs={'username': 'testuser1'}))
        self.assertEqual(self.community.get_absolute_url(), reverse('communities:detail', kwargs={'slug': 'python'}))
        self.assertEqual(
            self.post1.get_absolute_url(),
            reverse('posts:detail', kwargs={'community_slug': 'python', 'post_id': self.post1.id, 'post_slug': self.post1.slug})
        )

    def test_search_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], 'Введите поисковый запрос')

    def test_search_posts(self):
        # Create vote for post1 by user2
        PostVote.objects.create(user=self.user2, post=self.post1, value=1)
        self.client.login(username='testuser2', password='password123')

        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.post1.id)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.community.id)

    def test_search_users(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='testuser1', password='password123')

        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 2)

        # Verify is_following precalculation
        user2_in_results = [u for u in results if u.id == self.user2.id][0]
        self.assertTrue(user2_in_results.is_following)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_pagination(self):
        # Create 12 posts with 'Search' in title
        for i in range(12):
            Post.objects.create(
                title=f'Search Post {i}',
                author=self.user1,
                community=self.community
            )

        response_page1 = self.client.get(reverse('search:results'), {'q': 'Search', 'type': 'posts', 'page': 1})
        self.assertEqual(response_page1.status_code, 200)
        self.assertEqual(len(response_page1.context['results']), 10)

        response_page2 = self.client.get(reverse('search:results'), {'q': 'Search', 'type': 'posts', 'page': 2})
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context['results']), 3)
