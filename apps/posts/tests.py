from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.comments.models import Comment

User = get_user_model()


class PostDetailAndCommentTreeTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testpostsuser', password='password123')
        self.community = Community.objects.create(
            name='testpostscomm',
            slug='testpostscomm',
            description='Test community description',
            creator=self.user
        )
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Some post content.',
            author=self.user,
            community=self.community
        )

    def test_comment_tree_integrity(self):
        """
        Проверяет сохранение древовидной целостности комментариев.
        Удалённые комментарии должны отображаться, если у них есть неудалённые ответы.
        Удалённые комментарии БЕЗ неудалённых ответов должны скрываться.
        """
        # 1. Корневой комментарий 1 (активный)
        c1 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Active Root Comment'
        )
        # 2. Корневой комментарий 2 (удалённый, но с активным ответом)
        c2 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Deleted Root with active reply',
            is_deleted=True
        )
        # Ответ на c2 (активный)
        c2_reply = Comment.objects.create(
            post=self.post,
            parent=c2,
            author=self.user,
            content='Active Reply to deleted root'
        )
        # 3. Корневой комментарий 3 (удалённый и без активных ответов)
        c3 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Deleted Root without active reply',
            is_deleted=True
        )

        response = self.client.get(reverse('posts:detail', kwargs={
            'community_slug': self.community.slug,
            'post_id': self.post.id,
            'post_slug': self.post.slug
        }))
        self.assertEqual(response.status_code, 200)

        # Проверяем переданные комментарии в контексте
        comments_in_context = response.context['comments']

        # Должны отображаться c1 и c2, но не c3
        self.assertIn(c1, comments_in_context)
        self.assertIn(c2, comments_in_context)
        self.assertNotIn(c3, comments_in_context)

        # Проверим, что у c2 есть активный ответ c2_reply в replies
        c2_context_replies = c2.replies.all()
        self.assertIn(c2_reply, c2_context_replies)
