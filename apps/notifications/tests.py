from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.votes.models import PostVote
from apps.users.models import UserFollow
from apps.notifications.models import Notification

User = get_user_model()


class NotificationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.community = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Test community',
            creator=self.user1
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            content='Test Post Content',
            author=self.user1,
            community=self.community
        )

    def test_comment_post_notification_signal(self):
        Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Great post!'
        )
        notification = Notification.objects.filter(recipient=self.user1).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, 'comment_post')
        self.assertEqual(notification.sender, self.user2)

    def test_post_vote_notification_signal(self):
        PostVote.objects.create(
            user=self.user2,
            post=self.post,
            value=1
        )
        notification = Notification.objects.filter(recipient=self.user1, notification_type='upvote_post').first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.sender, self.user2)

    def test_follow_notification_signal(self):
        UserFollow.objects.create(
            follower=self.user2,
            following=self.user1
        )
        notification = Notification.objects.filter(recipient=self.user1, notification_type='follow').first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.sender, self.user2)

    def test_notification_badge_and_mark_read_views(self):
        Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='follow',
            message='started following you'
        )
        self.client.login(username='user1', password='password123')
        badge_url = reverse('notifications:badge')
        res = self.client.get(badge_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '1')

        mark_all_url = reverse('notifications:mark_all_read')
        res = self.client.post(mark_all_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 0)
