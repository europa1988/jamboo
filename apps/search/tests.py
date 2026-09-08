from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='search_user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='search_user2',
            email='user2@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='python_devs',
            slug='python_devs',
            description='Community for Python developers',
            creator=self.user1
        )
        self.post1 = Post.objects.create(
            title='Django Search Integration',
            slug='django-search-integration',
            content='Testing Django search views with HTMX suggestions',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Flask vs Django',
            slug='flask-vs-django',
            content='Comparing web frameworks in Python',
            author=self.user2,
            community=self.community
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')
        self.assertIsNone(response.context['results'])

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        results = response.context['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(response.context['total_count'], 2)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'python_devs')

    def test_search_results_users(self):
        response = self.client.get(reverse('search:results'), {'q': 'search_user', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        results = response.context['results']
        self.assertEqual(len(results), 2)

    def test_search_results_authenticated_vote_and_follow(self):
        self.client.login(username='search_user1', password='password123')
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # Test post user_vote
        res_posts = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        p1 = [p for p in res_posts.context['results'] if p.id == self.post1.id][0]
        self.assertEqual(p1.user_vote, PostVote.UPVOTE)

        # Test user is_following
        res_users = self.client.get(reverse('search:results'), {'q': 'search_user2', 'type': 'users'})
        u2 = res_users.context['results'][0]
        self.assertTrue(u2.is_following)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_matching_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        first_suggestion = suggestions[0]
        self.assertIn('url', first_suggestion)
        self.assertIn('type', first_suggestion)
        self.assertIn('title', first_suggestion)
        self.assertIn('subtitle', first_suggestion)
