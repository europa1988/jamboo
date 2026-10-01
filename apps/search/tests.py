from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='alice',
            password='password123',
            first_name='Alice',
            last_name='Wonder'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            password='password123',
            first_name='Bob',
            last_name='Builder'
        )

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming language community',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='Django 6.0 features',
            slug='django-60-features',
            content='Awesome new features in Django',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 tips',
            slug='python-312-tips',
            content='Performance tips in Python',
            author=self.user2,
            community=self.community
        )

    def test_search_results_default_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.post1, response.context['results'])

    def test_search_results_posts_authenticated(self):
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        self.client.force_login(self.user1)
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        post_in_ctx = response.context['results'][0]
        self.assertEqual(post_in_ctx, self.post2)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 1)
        self.assertIn(self.community, response.context['results'])

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        self.assertEqual(response.context['total_count'], 1)
        user_in_ctx = response.context['results'][0]
        self.assertTrue(user_in_ctx.is_following)

    def test_search_suggestions(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)

        types_found = {s['type'] for s in suggestions}
        self.assertIn('post', types_found)
        self.assertIn('community', types_found)

    def test_search_suggestions_short_query(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)
