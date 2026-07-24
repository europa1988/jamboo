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
        # Create users
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')
        self.user3 = User.objects.create_user(username='anotheruser', password='password123')

        # Create communities
        self.community1 = Community.objects.create(
            name='django',
            slug='django',
            description='Django discussion community',
            creator=self.user1
        )
        self.community2 = Community.objects.create(
            name='python',
            slug='python',
            description='Python discussion community',
            creator=self.user2
        )

        # Create posts
        self.post1 = Post.objects.create(
            title='Learning Django framework',
            slug='learning-django-framework',
            content='This is a post about Django.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Python patterns and practices',
            slug='python-patterns',
            content='All about python patterns.',
            author=self.user2,
            community=self.community2
        )
        self.post3 = Post.objects.create(
            title='Django best practices',
            slug='django-best-practices',
            content='Thorough guide to Django.',
            author=self.user1,
            community=self.community1
        )

        # Create user follow relationship
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Create post vote
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)
        PostVote.objects.create(user=self.user1, post=self.post3, value=PostVote.DOWNVOTE)

    def test_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], "Введите поисковый запрос")

    def test_post_search_anonymous(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], 'Django')
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 2)

        results = response.context['results']
        self.assertEqual(len(results), 2)
        for post in results:
            self.assertIsNone(post.user_vote)

    def test_post_search_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)

        results = list(response.context['results'])
        # Since ordering is -created_at, post3 is first, then post1
        self.assertEqual(results[0].id, self.post3.id)
        self.assertEqual(results[0].user_vote, PostVote.DOWNVOTE)
        self.assertEqual(results[1].id, self.post1.id)
        self.assertEqual(results[1].user_vote, PostVote.UPVOTE)

    def test_community_search(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        results = response.context['results']
        self.assertEqual(results[0].slug, 'python')

    def test_user_search(self):
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'testuser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)

        results = list(response.context['results'])
        # Users should be sorted alphabetically by username
        self.assertEqual(results[0].username, 'testuser1')
        self.assertEqual(results[1].username, 'testuser2')

        # Test followed status
        self.assertFalse(results[0].is_following) # Cannot follow yourself or is not following
        self.assertTrue(results[1].is_following) # user1 is following user2

    def test_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_suggestions_valid_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        # Should match post1, post3, and community1
        self.assertTrue(len(suggestions) > 0)

        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

        # Check keys
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)

    def test_results_pagination(self):
        # Create 11 additional Django posts to trigger pagination
        for i in range(11):
            Post.objects.create(
                title=f'Extra Django post {i}',
                slug=f'extra-django-post-{i}',
                content='Extra content',
                author=self.user1,
                community=self.community1
            )

        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 13) # 2 initial + 11 extra

        results = response.context['results']
        self.assertEqual(len(results), 10) # 10 items per page
        self.assertTrue(results.has_next())
        self.assertFalse(results.has_previous())

        # Fetch second page
        response_page2 = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts', 'page': 2})
        self.assertEqual(response_page2.status_code, 200)
        results_page2 = response_page2.context['results']
        self.assertEqual(len(results_page2), 3) # Remaining 3 items
