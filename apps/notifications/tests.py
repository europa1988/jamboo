from django.test import TestCase
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.votes.models import PostVote
from apps.notifications.models import Notification


class NotificationSignalsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='password123')
        self.community = Community.objects.create(name='testcomm', slug='testcomm', description='desc', creator=self.user1)
        self.post = Post.objects.create(title='Post 1', content='Content', author=self.user1, community=self.community)

    def test_comment_notification_signal(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Great post!'
        )
        notifications = Notification.objects.filter(recipient=self.user1, notification_type='comment_post')
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().sender, self.user2)

    def test_post_vote_notification_signal(self):
        PostVote.objects.create(user=self.user2, post=self.post, value=1)
        notifications = Notification.objects.filter(recipient=self.user1, notification_type='upvote_post')
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().sender, self.user2)
