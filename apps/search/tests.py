from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')

        self.community1 = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user1
        )

        self.post1 = Post.objects.create(
            title='Django 6.0 released',
            slug='django-60-released',
            content='Awesome features in Django',
            author=self.user1,
            community=self.community1
        )

    def test_search_results_posts(self):
        url = reverse('search:results') + '?q=Django&type=posts'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django 6.0 released')

    def test_search_results_communities(self):
        url = reverse('search:results') + '?q=python&type=communities'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/python')

    def test_search_results_users(self):
        url = reverse('search:results') + '?q=testuser&type=users'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/testuser1')

    def test_search_suggestions(self):
        url = reverse('search:suggestions') + '?q=Django'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django 6.0 released')
