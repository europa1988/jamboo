from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1,
            member_count=10
        )

        self.post = Post.objects.create(
            title='Django web development',
            slug='django-web-development',
            content='Awesome Django post',
            author=self.user1,
            community=self.community
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertIn('error', response.context)

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_posts_authenticated(self):
        self.client.login(username='testuser1', password='password123')
        PostVote.objects.create(user=self.user1, post=self.post, value=1)

        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results'][0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username='testuser1', password='password123')

        response = self.client.get(reverse('search:results'), {'q': 'testuser2', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertTrue(getattr(response.context['results'][0], 'is_following', False))

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_matching_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'testuser'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['suggestions']) >= 2)
