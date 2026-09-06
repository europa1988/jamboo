from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.comments.models import Comment
from apps.votes.models import PostVote
from apps.notifications.models import Notification

User = get_user_model()


class NotificationViewsAndSignalsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        self.community = Community.objects.create(
            name='general',
            slug='general',
            description='General discussions',
            creator=self.user1
        )

        self.post = Post.objects.create(
            title='First Post',
            slug='first-post',
            content='Hello world',
            author=self.user1,
            community=self.community
        )

    def test_comment_signal_creates_notification(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Great post!'
        )
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.user1)
        self.assertEqual(notif.sender, self.user2)
        self.assertEqual(notif.notification_type, 'comment_post')

    def test_post_vote_signal_creates_notification(self):
        PostVote.objects.create(
            user=self.user2,
            post=self.post,
            value=1
        )
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.user1)
        self.assertEqual(notif.notification_type, 'upvote_post')

    def test_notification_badge_and_mark_read_views(self):
        Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='comment_post',
            message='test notification'
        )

        self.client.login(username='alice', password='password123')

        # Test badge
        url_badge = reverse('notifications:badge')
        response = self.client.get(url_badge)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unread_count'], 1)

        # Test mark read
        notif = Notification.objects.first()
        url_read = reverse('notifications:mark_read', kwargs={'notification_id': notif.id})
        response = self.client.post(url_read)
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
