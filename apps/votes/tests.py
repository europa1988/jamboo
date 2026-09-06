from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.comments.models import Comment
from apps.votes.models import PostVote, CommentVote

User = get_user_model()


class VoteViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='voter', password='password123')
        self.community = Community.objects.create(
            name='news', slug='news', description='News', creator=self.user
        )
        self.post = Post.objects.create(
            title='Vote Test Post', slug='vote-test-post', content='Content', author=self.user, community=self.community
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content='Vote test comment'
        )

    def test_vote_post_upvote_and_toggle(self):
        self.client.login(username='voter', password='password123')
        url = reverse('votes:post', kwargs={'post_id': self.post.id})

        # Upvote
        response = self.client.post(url, {'action': 'up'})
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        self.assertEqual(PostVote.objects.filter(user=self.user, post=self.post).count(), 1)

        # Upvote again (toggle off)
        response = self.client.post(url, {'action': 'up'})
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 0)
        self.assertEqual(PostVote.objects.filter(user=self.user, post=self.post).count(), 0)

    def test_vote_comment_downvote(self):
        self.client.login(username='voter', password='password123')
        url = reverse('votes:comment', kwargs={'comment_id': self.comment.id})

        response = self.client.post(url, {'action': 'down'})
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)
        self.assertEqual(CommentVote.objects.filter(user=self.user, comment=self.comment).count(), 1)
