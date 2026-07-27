from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community, CommunityMember
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


class SearchTests(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=20)

        # Create communities
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Django community',
            creator=self.user1,
            member_count=1
        )
        CommunityMember.objects.create(
            user=self.user1,
            community=self.community,
            role='admin'
        )

        # Create posts
        self.post = Post.objects.create(
            title='How to search in Django',
            slug='how-to-search-in-django',
            content='This is a tutorial on searching.',
            author=self.user1,
            community=self.community,
            post_type='text'
        )

        # Create votes
        self.vote = PostVote.objects.create(
            user=self.user2,
            post=self.post,
            value=PostVote.UPVOTE
        )

    def test_search_results_empty_query(self):
        response = self.client.get(reverse('search:results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/results.html')
        self.assertEqual(len(response.context['results']), 0)

    def test_search_posts_not_authenticated(self):
        response = self.client.get(reverse('search:results'), {'q': 'search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['results'])
        # Check that post in results has user_vote set to None
        results = list(response.context['results'])
        self.assertIsNone(results[0].user_vote)

    def test_search_posts_authenticated_with_vote(self):
        self.client.force_login(self.user2)
        response = self.client.get(reverse('search:results'), {'q': 'search', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_vote, PostVote.UPVOTE)

    def test_search_communities(self):
        response = self.client.get(reverse('search:results'), {'q': 'django', 'type': 'communities'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.community, response.context['results'])

    def test_search_users_not_following(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].is_following)

    def test_search_users_following(self):
        # Alice follows Bob
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        self.client.force_login(self.user1)
        response = self.client.get(reverse('search:results'), {'q': 'bob', 'type': 'users'})
        self.assertEqual(response.status_code, 200)
        results = list(response.context['results'])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_following)

    def test_search_suggestions_too_short(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_suggestions_valid(self):
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggestions']
        self.assertGreaterEqual(len(suggestions), 1)

        # Verify that all returned suggestions have the required keys
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)
            self.assertIn(item['type'], ['post', 'community', 'user'])
