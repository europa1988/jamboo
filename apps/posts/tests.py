from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment


class CommentTreeIntegrityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="treeuser", email="treeuser@test.com", password="password123")
        self.community = Community.objects.create(
            name="treecommunity",
            slug="treecommunity",
            description="Testing comment trees",
            creator=self.user
        )
        self.post = Post.objects.create(
            title="Tree Post",
            slug="tree-post",
            content="Tree post content",
            author=self.user,
            community=self.community
        )

        # Create comment tree:
        # parent1 (active) -> reply1_1 (deleted) -> reply1_1_1 (active)
        # parent2 (deleted, but has NO active replies)
        self.parent1 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="parent 1",
            is_deleted=False
        )
        self.reply1_1 = Comment.objects.create(
            post=self.post,
            parent=self.parent1,
            author=self.user,
            content="reply 1-1",
            is_deleted=True
        )
        self.reply1_1_1 = Comment.objects.create(
            post=self.post,
            parent=self.reply1_1,
            author=self.user,
            content="reply 1-1-1",
            is_deleted=False
        )

        self.parent2 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="parent 2",
            is_deleted=True
        )

    def test_comment_tree_inclusion(self):
        # Request the post detail page
        url = reverse('posts:detail', kwargs={
            'community_slug': self.community.slug,
            'post_id': self.post.id,
            'post_slug': self.post.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # The context 'comments' should have parent1
        comments = response.context['comments']
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].id, self.parent1.id)

        # Under parent1, there should be reply1_1 (even though it's deleted, because it has reply1_1_1 which is active)
        replies_of_parent1 = comments[0].replies.all()
        self.assertEqual(len(replies_of_parent1), 1)
        self.assertEqual(replies_of_parent1[0].id, self.reply1_1.id)

        # Under reply1_1, there should be reply1_1_1
        replies_of_reply1_1 = replies_of_parent1[0].replies.all()
        self.assertEqual(len(replies_of_reply1_1), 1)
        self.assertEqual(replies_of_reply1_1[0].id, self.reply1_1_1.id)

        # parent2 should be completely excluded from the top-level comments because it's deleted and has no active replies
        self.assertNotIn(self.parent2, comments)

    def test_comment_replies_descriptor_restored(self):
        # Verify that original Comment.replies descriptor is unmodified before and after requests
        from apps.posts.views import original_replies_descriptor
        self.assertEqual(Comment.replies, original_replies_descriptor)

        url = reverse('posts:detail', kwargs={
            'community_slug': self.community.slug,
            'post_id': self.post.id,
            'post_slug': self.post.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # It should still be original class descriptor after request ends (restored in finally block)
        self.assertEqual(Comment.replies, original_replies_descriptor)
