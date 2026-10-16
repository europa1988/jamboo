from django.test import TestCase
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=50)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=100)

        # User profiles are auto-created via signals
        self.user1.profile.bio = 'Python developer and tech enthusiast'
        self.user1.profile.save()

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='All about Python programming language',
            creator=self.user1,
            member_count=10
        )

        self.post1 = Post.objects.create(
            title='Welcome to Python Community',
            slug='welcome-to-python-community',
            content='This is a discussion post about Django and Python.',
            author=self.user1,
            community=self.community
        )

        self.post2 = Post.objects.create(
            title='Learning Django framework',
            slug='learning-django-framework',
            content='Django makes web development easy.',
            author=self.user2,
            community=self.community
        )

    def test_search_results_posts(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)
        self.assertIn(self.post1, response.context['results'])
        self.assertIn(self.post2, response.context['results'])

    def test_search_results_posts_authenticated_vote(self):
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)
        self.client.login(username='alice', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['results'])
        vote_dict = {p.id: getattr(p, 'user_vote', None) for p in posts}
        self.assertEqual(vote_dict.get(self.post1.id), 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'programming', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'developer', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['results'][0], self.user1)

    def test_search_results_users_is_following(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='alice', password='password123')
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        users = list(response.context['results'])
        self.assertTrue(getattr(users[0], 'is_following', False))

    def test_search_suggestions_endpoint(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) >= 1)
        first_suggestion = suggestions[0]
        self.assertIn('url', first_suggestion)
        self.assertIn('type', first_suggestion)
        self.assertIn('title', first_suggestion)
        self.assertIn('subtitle', first_suggestion)
