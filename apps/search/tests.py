from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserFollow
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='john_doe', password='password123')
        self.user2 = User.objects.create_user(username='jane_smith', password='password123')

        self.user1.profile.bio = 'Software Developer'
        self.user1.profile.save()
        self.user2.profile.bio = 'Graphic Designer'
        self.user2.profile.save()

        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='All about Python programming',
            creator=self.user1,
            member_count=10,
            is_active=True
        )

        self.post = Post.objects.create(
            title='Django 6.0 Features',
            content='Awesome new features in Django 6.0',
            author=self.user1,
            community=self.community
        )

        PostVote.objects.create(user=self.user1, post=self.post, value=1)
        UserFollow.objects.create(follower=self.user1, following=self.user2)

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_short_query(self):
        response = self.client.get(reverse('search:results'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'минимум 2 символа')

    def test_search_results_posts(self):
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_posts_authenticated_vote(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        post_item = response.context['results'][0]
        self.assertEqual(getattr(post_item, 'user_vote', None), 1)

    def test_search_results_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'python', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('search:results'), {'q': 'jane', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        user_item = response.context['results'][0]
        self.assertEqual(user_item, self.user2)
        self.assertTrue(getattr(user_item, 'is_following', False))

    def test_search_suggestions(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'py'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.context)
        suggestions = response.context['suggestions']
        self.assertTrue(any(s['type'] == 'community' and 'python' in s['title'] for s in suggestions))
