from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.profile.bio = 'Test bio for user'
        self.user.profile.save()

        self.other_user = User.objects.create_user(username='otheruser', password='password123')
        self.other_user.profile.bio = 'Another bio'
        self.other_user.profile.save()

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python programming language community',
            creator=self.user,
            member_count=10
        )

        self.post = Post.objects.create(
            title='Django 6.0 Released',
            slug='django-60-released',
            content='Awesome features in Django 6.0',
            author=self.user,
            community=self.community
        )

        PostVote.objects.create(
            user=self.user,
            post=self.post,
            value=1
        )

    def test_search_results_posts_unauthenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.post)
        self.assertIsNone(results[0].user_vote)

    def test_search_results_posts_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'Python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.community)

    def test_search_results_users(self):
        UserFollow.objects.create(follower=self.user, following=self.other_user)
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('search:results'), {'q': 'otheruser', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.other_user)
        self.assertTrue(results[0].is_following)

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/partials/suggestions.html')
        self.assertContains(response, 'Django 6.0 Released')

    def test_search_suggestions_short_query(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Django 6.0 Released')
