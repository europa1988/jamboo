from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post

User = get_user_model()


class VotesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='voter', password='password123')
        self.community = Community.objects.create(
            name='votecomm',
            slug='votecomm',
            description='Vote community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Votable Post',
            content='Votable Post Content',
            author=self.user,
            community=self.community
        )

    def test_vote_post_toggle(self):
        self.client.login(username='voter', password='password123')
        vote_url = reverse('votes:post', kwargs={'post_id': self.post.id})

        # Upvote (HTMX request)
        res = self.client.post(vote_url, {'action': 'up'}, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

        # Remove Upvote by voting up again
        res = self.client.post(vote_url, {'action': 'up'}, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 0)
