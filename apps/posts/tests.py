from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community
from apps.posts.models import Post

User = get_user_model()


class PostsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='password123')
        self.community = Community.objects.create(
            name='general',
            slug='general',
            description='General community',
            creator=self.user
        )

    def test_post_auto_slug_and_get_absolute_url(self):
        post = Post.objects.create(
            title='Тестовый Заголовок Поста',
            content='Содержимое поста',
            author=self.user,
            community=self.community
        )
        self.assertTrue(bool(post.slug))
        self.assertEqual(
            post.get_absolute_url(),
            reverse('posts:detail', kwargs={
                'community_slug': 'general',
                'post_id': post.id,
                'post_slug': post.slug
            })
        )

    def test_home_view(self):
        Post.objects.create(
            title='Home Post Title',
            content='Home Post Content',
            author=self.user,
            community=self.community
        )
        response = self.client.get(reverse('posts:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Home Post Title')
