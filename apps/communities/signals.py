from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CommunityMember


@receiver(post_save, sender=CommunityMember)
def increment_member_count(sender, instance, created, **kwargs):
    if created:
        instance.community.member_count += 1
        instance.community.save(update_fields=['member_count'])


@receiver(post_delete, sender=CommunityMember)
def decrement_member_count(sender, instance, **kwargs):
    instance.community.member_count = max(0, instance.community.member_count - 1)
    instance.community.save(update_fields=['member_count'])