import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from apps.comments.models import Comment
from apps.votes.models import PostVote, CommentVote
from apps.users.models import UserFollow
from .models import Notification


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """
    Создаёт уведомление при ответе на комментарий или комментарии к посту.
    """
    if not created:
        return
    
    comment = instance
    
    # Уведомление автору поста о новом комментарии
    if comment.parent is None and comment.post.author != comment.author:
        Notification.objects.create(
            recipient=comment.post.author,
            sender=comment.author,
            notification_type='comment_post',
            content_object=comment,
            message=f'прокомментировал ваш пост "{comment.post.title[:50]}"'
        )
    
    # Уведомление автору родительского комментария о ответе
    if comment.parent and comment.parent.author != comment.author:
        Notification.objects.create(
            recipient=comment.parent.author,
            sender=comment.author,
            notification_type='reply',
            content_object=comment,
            message=f'ответил на ваш комментарий'
        )


@receiver(post_save, sender=PostVote)
def create_post_vote_notification(sender, instance, created, **kwargs):
    """
    Уведомление автору поста о голосе (только апвоут).
    """
    if not created or instance.value != 1:
        return
    
    # Не уведомляем о собственных голосах
    if instance.post.author == instance.user:
        return
    
    # Расчёт временного порога (5 минут назад)
    threshold = instance.created_at - datetime.timedelta(minutes=5)

    # Получаем ContentType для Post
    post_type = ContentType.objects.get_for_model(instance.post)

    # Проверяем, не было ли уже уведомления недавно (чтобы не спамить)
    recent = Notification.objects.filter(
        recipient=instance.post.author,
        sender=instance.user,
        notification_type='upvote_post',
        content_type=post_type,
        object_id=instance.post.id,
        created_at__gte=threshold
    ).exists()
    
    if not recent:
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.user,
            notification_type='upvote_post',
            content_object=instance.post,
            message=f'оценил ваш пост "{instance.post.title[:50]}"'
        )


@receiver(post_save, sender=CommentVote)
def create_comment_vote_notification(sender, instance, created, **kwargs):
    """
    Уведомление автору комментария о голосе (только апвоут).
    """
    if not created or instance.value != 1:
        return
    
    if instance.comment.author == instance.user:
        return
    
    Notification.objects.create(
        recipient=instance.comment.author,
        sender=instance.user,
        notification_type='upvote_comment',
        content_object=instance.comment,
        message='оценил ваш комментарий'
    )


@receiver(post_save, sender=UserFollow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Уведомление о новом подписчике.
    """
    if not created:
        return
    
    Notification.objects.create(
        recipient=instance.following,
        sender=instance.follower,
        notification_type='follow',
        message='подписался на вас'
    )