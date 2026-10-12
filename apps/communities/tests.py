from django.test import TestCase
from django.urls import reverse
from apps.users.models import User
from apps.communities.models import Community


class CommunityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='commuser',
            email='commuser@example.com',
            password='password123'
        )
        self.community = Community.objects.create(
            name='django',
            slug='django',
            description='Django discussion',
            creator=self.user
        )

    def test_community_fields_and_methods(self):
        self.assertTrue(self.community.is_active)
        expected_url = reverse('communities:detail', kwargs={'slug': 'django'})
        self.assertEqual(self.community.get_absolute_url(), expected_url)
