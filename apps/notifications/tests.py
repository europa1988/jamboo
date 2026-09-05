from django.test import TestCase
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.votes.models import PostVote
from apps.notifications.models import Notification


class NotificationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            creator=self.user1
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            author=self.user1,
            community=self.community
        )

    def test_comment_post_notification(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Great post!'
        )
        noti = Notification.objects.filter(recipient=self.user1, notification_type='comment_post').first()
        self.assertIsNotNone(noti)
        self.assertEqual(noti.sender, self.user2)

    def test_post_vote_notification(self):
        vote = PostVote.objects.create(
            user=self.user2,
            post=self.post,
            value=1
        )
        noti = Notification.objects.filter(recipient=self.user1, notification_type='upvote_post').first()
        self.assertIsNotNone(noti)
        self.assertEqual(noti.sender, self.user2)
