from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.votes.models import CommentVote


class PostAndCommentViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем пользователей
        self.user = User.objects.create_user(
            username='test_posts_user',
            email='test_posts@example.com',
            password='password123'
        )

        # Создаем сообщество
        self.community = Community.objects.create(
            name='PostsCommunity',
            slug='posts-community',
            description='Test community for posts and comments',
            creator=self.user
        )

        # Создаем пост
        self.post = Post.objects.create(
            title='Test Post Title',
            slug='test-post-title',
            content='Test Post Content',
            author=self.user,
            community=self.community
        )

    def test_comment_tree_integrity(self):
        """
        Проверяем целостность дерева комментариев (Comment Tree Integrity):
        Удаленные комментарии верхнего уровня должны включаться в выборку,
        если у них есть активные ответы.
        """
        # 1. Топ-уровень, удален, но есть активный ответ (должен присутствовать в выдаче)
        deleted_with_replies = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Deleted parent',
            parent=None,
            is_deleted=True
        )
        active_reply = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Active reply',
            parent=deleted_with_replies
        )

        # 2. Топ-уровень, удален и нет ответов (должен быть отфильтрован и отсутствовать)
        deleted_without_replies = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Deleted orphan',
            parent=None,
            is_deleted=True
        )

        # 3. Топ-уровень, активен (должен присутствовать)
        active_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Active comment',
            parent=None
        )

        # Переходим на детальную страницу поста
        url = reverse('posts:detail', kwargs={
            'community_slug': self.community.slug,
            'post_id': self.post.id,
            'post_slug': self.post.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        comments = response.context['comments']

        # Должны быть возвращены deleted_with_replies и active_comment, но не deleted_without_replies
        comment_ids = [c.id for c in comments]
        self.assertIn(deleted_with_replies.id, comment_ids)
        self.assertIn(active_comment.id, comment_ids)
        self.assertNotIn(deleted_without_replies.id, comment_ids)

    def test_comment_vote_prefetch(self):
        """
        Проверяем, что голоса за комментарии предвыбираются (prefetch)
        для авторизованного пользователя.
        """
        active_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Testing prefetch comment',
            parent=None
        )

        # Ставим апвоут
        CommentVote.objects.create(
            user=self.user,
            comment=active_comment,
            value=CommentVote.UPVOTE
        )

        # Авторизуемся
        self.client.login(username='test_posts_user', password='password123')

        url = reverse('posts:detail', kwargs={
            'community_slug': self.community.slug,
            'post_id': self.post.id,
            'post_slug': self.post.slug
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        comments = response.context['comments']
        c_obj = [c for c in comments if c.id == active_comment.id][0]

        # Должен быть проставлен user_vote
        self.assertEqual(c_obj.user_vote, CommentVote.UPVOTE)
