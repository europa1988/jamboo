from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=50)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=100)

        # Create user profiles (Django signal might create them automatically, so let's update them)
        profile1 = self.user1.profile
        profile1.bio = "Python developer and enthusiast"
        profile1.save()

        profile2 = self.user2.profile
        profile2.bio = "Django master"
        profile2.save()

        # Create communities
        self.community_python = Community.objects.create(
            name='python',
            slug='python',
            description='Community for Python developers',
            creator=self.user1,
            member_count=10
        )
        self.community_django = Community.objects.create(
            name='django',
            slug='django',
            description='Community for Django developers',
            creator=self.user2,
            member_count=5
        )

        # Create posts
        self.post1 = Post.objects.create(
            title='Python 3.12 release notes',
            slug='python-312-release-notes',
            content='Let us discuss new features of Python 3.12.',
            author=self.user1,
            community=self.community_python
        )
        self.post2 = Post.objects.create(
            title='Django 6.0 features',
            slug='django-60-features',
            content='Django 6.0 brings many changes.',
            author=self.user2,
            community=self.community_django
        )

    def test_search_results_posts_unauthenticated(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python 3.12 release notes')
        self.assertNotContains(response, 'Django 6.0 features')
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)

    def test_search_results_posts_authenticated_with_vote(self):
        self.client.login(username='alice', password='password123')
        # Create a vote for post1
        PostVote.objects.create(user=self.user1, post=self.post1, value=1)

        url = reverse('search:results')
        response = self.client.get(url, {'q': 'Python', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python 3.12 release notes')
        # Check that user_vote was attached correctly
        results = response.context['results']
        self.assertEqual(results[0].user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'developer', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'c/python')
        self.assertContains(response, 'c/django')
        self.assertEqual(len(response.context['results']), 2)

    def test_search_results_users(self):
        url = reverse('search:results')
        response = self.client.get(url, {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'u/bob')
        self.assertNotContains(response, 'u/alice')
        self.assertEqual(len(response.context['results']), 1)

    def test_search_suggestions_length_gte_2(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        # Should match post1 title, community_python, and user1 username
        self.assertContains(response, 'Python 3.12 release notes')
        self.assertContains(response, 'c/python')
        self.assertContains(response, 'u/alice')

    def test_search_suggestions_length_lt_2(self):
        url = reverse('search:suggestions')
        response = self.client.get(url, {'q': 'p'})
        self.assertEqual(response.status_code, 200)
        # Should render empty or suggestions block should not be rendered
        self.assertNotContains(response, 'Python 3.12 release notes')
