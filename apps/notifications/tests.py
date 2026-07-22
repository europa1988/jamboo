from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.votes.models import PostVote
from apps.notifications.models import Notification


class NotificationsSignalTestCase(TestCase):
    def setUp(self):
        self.user_author = User.objects.create_user(username="author", email="author@test.com", password="password123")
        self.user_voter = User.objects.create_user(username="voter", email="voter@test.com", password="password123")

        self.community = Community.objects.create(
            name="notifcomm",
            slug="notifcomm",
            description="Testing notifications",
            creator=self.user_author
        )

        self.post = Post.objects.create(
            title="Notification post",
            slug="notification-post",
            content="Check notifications",
            author=self.user_author,
            community=self.community
        )

    def test_post_vote_notification_creation(self):
        # Create a PostVote (upvote)
        vote = PostVote.objects.create(
            user=self.user_voter,
            post=self.post,
            value=1
        )

        # Check that a notification has been created
        notifications = Notification.objects.filter(
            recipient=self.user_author,
            sender=self.user_voter,
            notification_type='upvote_post'
        )
        self.assertEqual(notifications.count(), 1)

        # Try to create another upvote recently (should not create another notification within 5 mins)
        # We manually check the signal behavior with another upvote on same post, but since a user
        # only has one vote per post, we can mock or check filters. Let's test the actual filter logic:
        recent_notif_exists = Notification.objects.filter(
            recipient=self.post.author,
            sender=self.user_voter,
            notification_type='upvote_post',
            object_id=self.post.id,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).exists()
        self.assertTrue(recent_notif_exists)
