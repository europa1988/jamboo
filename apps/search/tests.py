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
        self.user1 = User.objects.create_user(username='alice', password='password123', karma=10)
        self.user2 = User.objects.create_user(username='bob', password='password123', karma=20)
        self.user3 = User.objects.create_user(username='charlie', password='password123', karma=30)

        # Create a community
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Django framework community',
            creator=self.user1,
            member_count=100,
            is_active=True
        )

        # Create posts
        self.posts = []
        for i in range(12):
            post = Post.objects.create(
                title=f'Django Tip #{i:02d}',
                slug=f'django-tip-{i}',
                content=f'This is the content for tip {i}',
                author=self.user1,
                community=self.community,
                post_type='text'
            )
            self.posts.append(post)

        # Create post votes
        PostVote.objects.create(user=self.user1, post=self.posts[11], value=1)
        PostVote.objects.create(user=self.user2, post=self.posts[11], value=-1)

    def test_search_suggestions_with_matching_query(self):
        """Test that search_suggestions returns expected keys and content for matching queries."""
        response = self.client.get(reverse('search:suggestions'), {'q': 'django'})
        self.assertEqual(response.status_code, 200)

        suggestions = response.context['suggestions']
        self.assertTrue(len(suggestions) > 0)

        # Check keys for each type of suggestion
        for item in suggestions:
            self.assertIn('url', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('subtitle', item)

            # Check type validity
            self.assertIn(item['type'], ['post', 'community', 'user'])

            if item['type'] == 'post':
                self.assertIn('Django Tip', item['title'])
            elif item['type'] == 'community':
                self.assertEqual(item['title'], 'c/django')

        # Querying specifically for a user
        response_user = self.client.get(reverse('search:suggestions'), {'q': 'bob'})
        self.assertEqual(response_user.status_code, 200)
        suggestions_user = response_user.context['suggestions']
        self.assertTrue(any(item['type'] == 'user' and item['title'] == 'u/bob' for item in suggestions_user))

    def test_search_suggestions_too_short(self):
        """Test that query less than 2 characters returns empty suggestions."""
        response = self.client.get(reverse('search:suggestions'), {'q': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['suggestions']), 0)

    def test_search_results_pagination(self):
        """Test that search_results enforces 10-item pagination."""
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_type'], 'posts')
        self.assertEqual(response.context['total_count'], 12)

        # Check first page pagination size
        page_obj = response.context['results']
        self.assertEqual(len(page_obj.object_list), 10)
        self.assertTrue(page_obj.has_next())

        # Check second page
        response_page2 = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts', 'page': 2})
        self.assertEqual(response_page2.status_code, 200)
        page_obj2 = response_page2.context['results']
        self.assertEqual(len(page_obj2.object_list), 2)
        self.assertFalse(page_obj2.has_next())

    def test_search_results_prefetching_votes_authenticated(self):
        """Test that user_vote attribute is set on returned posts for authenticated users to avoid N+1 queries."""
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context['results']
        posts = page_obj.object_list

        # For the last created post (index 11), which is on the first page, alice voted +1
        first_post = next(p for p in posts if p.id == self.posts[11].id)
        self.assertEqual(first_post.user_vote, 1)

        # For another post (index 10), which is on the first page, alice hasn't voted
        second_post = next(p for p in posts if p.id == self.posts[10].id)
        self.assertIsNone(second_post.user_vote)

    def test_search_results_prefetching_votes_anonymous(self):
        """Test that user_vote is None for anonymous users."""
        response = self.client.get(reverse('search:results'), {'q': 'Django', 'type': 'posts'})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context['results']
        posts = page_obj.object_list
        for post in posts:
            self.assertIsNone(post.user_vote)

    def test_search_results_user_ordering(self):
        """Test that search results for users are explicitly and alphabetically ordered by username."""
        response = self.client.get(reverse('search:results'), {'q': 'a', 'type': 'users'})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context['results']
        users_found = page_obj.object_list

        # Should contain alice and charlie (both have 'a' in username)
        usernames = [u.username for u in users_found]
        self.assertIn('alice', usernames)
        self.assertIn('charlie', usernames)

        # Ordering must be alphabetical: alice, then charlie
        sorted_usernames = sorted(usernames)
        self.assertEqual(usernames, sorted_usernames)
