from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


class SearchViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='searchuser', password='password123')
        self.user.profile.bio = 'Python developer'
        self.user.profile.save()
        self.user2 = User.objects.create_user(username='otheruser', password='password123')
        self.community = Community.objects.create(
            name='python',
            slug='python',
            description='Python community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Django search test post',
            content='This is a post content for search',
            author=self.user,
            community=self.community
        )

    def test_search_results_empty_query(self):
        url = reverse('search:results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите поисковый запрос')

    def test_search_results_posts(self):
        url = reverse('search:results') + '?q=Django&type=posts'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.post)

    def test_search_results_authenticated_vote(self):
        PostVote.objects.create(user=self.user, post=self.post, value=1)
        self.client.login(username='searchuser', password='password123')
        url = reverse('search:results') + '?q=Django&type=posts'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        item = response.context['results'][0]
        self.assertEqual(item.user_vote, 1)

    def test_search_results_communities(self):
        url = reverse('search:results') + '?q=python&type=communities'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.community)

    def test_search_results_users(self):
        url = reverse('search:results') + '?q=searchuser&type=users'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['results'][0], self.user)

    def test_search_suggestions(self):
        url = reverse('search:suggestions') + '?q=Django'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]['type'], 'post')
        self.assertEqual(suggestions[0]['title'], self.post.title)
