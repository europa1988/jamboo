from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.communities.models import Community, CommunityMember

User = get_user_model()


class CommunitiesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commuser', password='password123')

    def test_community_absolute_url_and_is_active(self):
        comm = Community.objects.create(
            name='django',
            slug='django',
            description='Django lovers',
            creator=self.user,
            is_active=True
        )
        self.assertTrue(comm.is_active)
        self.assertEqual(comm.get_absolute_url(), '/c/django/')

    def test_community_join_and_leave(self):
        comm = Community.objects.create(
            name='testcomm',
            slug='testcomm',
            description='Test community',
            creator=self.user
        )
        user2 = User.objects.create_user(username='joiner', password='password123')
        self.client.login(username='joiner', password='password123')

        join_url = reverse('communities:join', kwargs={'slug': 'testcomm'})
        res = self.client.post(join_url, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(CommunityMember.objects.filter(user=user2, community=comm).exists())

        leave_url = reverse('communities:leave', kwargs={'slug': 'testcomm'})
        res = self.client.post(leave_url, HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(CommunityMember.objects.filter(user=user2, community=comm).exists())
