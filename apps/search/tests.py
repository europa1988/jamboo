from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', karma=100)
        self.other_user = User.objects.create_user(username='john_doe', password='password123', karma=50)

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming community',
            creator=self.user,
            member_count=10
        )
        self.community2 = Community.objects.create(
            name='django',
            slug='django',
            description='Django web framework community',
            creator=self.user,
            member_count=20
        )

        self.post1 = Post.objects.create(
            title='Django tutorial for beginners',
            slug='django-tutorial',
            content='Learn Django web framework step by step',
            author=self.user,
            community=self.community2,
        )
        self.post2 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312',
            content='New features in Python 3.12',
            author=self.other_user,
            community=self.community,
        )

        PostVote.objects.create(
            user=self.user,
            post=self.post1,
            value=PostVote.UPVOTE
        )

    def test_search_results_default_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(list(response.context['results']), [self.post1])

    def test_search_results_authenticated_post_votes(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'community', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'communities')
        self.assertEqual(response.context['total_count'], 2)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user, following=self.other_user)
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'john', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'users')
        users = list(response.context['results'])
        self.assertEqual(len(users), 1)
        self.assertTrue(users[0].is_following)

    def test_search_suggestions_endpoint(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)
        types = [item['type'] for item in suggestions]
        self.assertIn('post', types)
        self.assertIn('community', types)

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['suggestions'], [])
