from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python discussion community',
            creator=self.user1,
            member_count=5
        )

        self.post1 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312-release-notes',
            content='Awesome new features in Python 3.12',
            author=self.user1,
            community=self.community
        )
        self.post2 = Post.objects.create(
            title='Django web development',
            slug='django-web-development',
            content='Building web apps with Django',
            author=self.user2,
            community=self.community
        )

        # Alice votes on post1
        PostVote.objects.create(user=self.user1, post=self.post1, value=PostVote.UPVOTE)
        # Alice follows Bob
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post1)

    def test_search_results_posts_user_vote(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = list(response.context['results'])
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self.user2)
        self.assertTrue(users[0].is_following)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 2)
        types = [s['type'] for s in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)
