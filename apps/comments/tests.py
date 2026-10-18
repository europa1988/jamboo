from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment

User = get_user_model()


class CommentsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='password123')
        self.community = Community.objects.create(
            name='commcomm',
            slug='commcomm',
            description='Comments community',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Commentable Post',
            content='Commentable Post Content',
            author=self.user,
            community=self.community
        )

    def test_create_and_delete_comment(self):
        self.client.login(username='commenter', password='password123')
        create_url = reverse('comments:create', kwargs={'post_id': self.post.id})

        res = self.client.post(create_url, {'content': 'This is a test comment'})
        self.assertEqual(res.status_code, 302)
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.content, 'This is a test comment')

        delete_url = reverse('comments:delete', kwargs={'comment_id': comment.id})
        res = self.client.post(delete_url)
        self.assertEqual(res.status_code, 302)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)
