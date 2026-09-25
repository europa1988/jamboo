from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='john_doe', password='password123')

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming language community',
            creator=self.user1
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django framework discussions',
            creator=self.user2
        )

        self.post1 = Post.objects.create(
            title='Welcome to Python',
            slug='welcome-to-python',
            content='This is a post about Python.',
            author=self.user1,
            community=self.community1
        )
        self.post2 = Post.objects.create(
            title='Django best practices',
            slug='django-best-practices',
            content='Here are some Django tips.',
            author=self.user2,
            community=self.community2
        )

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community2)

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'john', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.user2)

    def test_search_results_user_vote_and_follow(self):
        self.client.login(username='testuser1', password='password123')
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        response_post = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        post_item = response_post.context['results'][0]
        self.assertEqual(post_item.user_vote, 1)

        response_user = self.client.get(reverse('search:results'), {'q': 'john', 'type': 'users'})
        user_item = response_user.context['results'][0]
        self.assertTrue(user_item.is_following)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)

        response_short = self.client.get(reverse('search:suggestions'), {'q': 'P'})
        self.assertEqual(response_short.status_code, 200)
        self.assertEqual(len(response_short.context['suggestions']), 0)
