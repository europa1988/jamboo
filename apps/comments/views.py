from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from apps.posts.models import Post
from .models import Comment
from .forms import CommentCreateForm, CommentEditForm


@login_required
def comment_create(request, post_id):
    """
    Создание комментария (верхнего уровня или ответа).
    """
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    if request.method != 'POST':
        return redirect('posts:detail',
                      community_slug=post.community.slug,
                      post_id=post.id,
                      post_slug=post.slug)
    
    form = CommentCreateForm(request.POST)
    if not form.is_valid():
        if request.headers.get('HX-Request'):
            return HttpResponseBadRequest('Ошибка в форме: ' + str(form.errors))
        messages.error(request, 'Исправьте ошибки в форме.')
        return redirect('posts:detail',
                      community_slug=post.community.slug,
                      post_id=post.id,
                      post_slug=post.slug)
    
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    
    # Проверяем parent_id (ответ на комментарий)
    parent_id = request.POST.get('parent_id')
    if parent_id:
        try:
            parent = Comment.objects.get(id=int(parent_id), post=post)
            comment.parent = parent
        except (Comment.DoesNotExist, ValueError):
            if request.headers.get('HX-Request'):
                return HttpResponseBadRequest('Родительский комментарий не найден.')
            messages.error(request, 'Родительский комментарий не найден.')
            return redirect('posts:detail',
                          community_slug=post.community.slug,
                          post_id=post.id,
                          post_slug=post.slug)
    
    comment.save()
    
    # Увеличиваем счётчик комментариев у поста
    post.comment_count = post.comments.filter(is_deleted=False).count()
    post.save()
    
    # Уведомление создаётся автоматически через сигналы
    
    # Если HTMX-запрос — возвращаем HTML нового комментария
    if request.headers.get('HX-Request'):
        return render(request, 'comments/partials/comment.html', {
            'comment': comment,
            'user': request.user,
            'post': post
        })
    
    messages.success(request, 'Комментарий добавлен!')
    return redirect('posts:detail',
                  community_slug=post.community.slug,
                  post_id=post.id,
                  post_slug=post.slug)


@login_required
def comment_reply_form(request, comment_id):
    """
    Возвращает форму ответа на комментарий (для HTMX).
    """
    parent_comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    post = parent_comment.post
    
    # Проверяем, что комментарий не слишком глубоко вложен
    if parent_comment.depth >= 7:
        return HttpResponseBadRequest('Максимальная вложенность достигнута.')
    
    form = CommentCreateForm()
    
    return render(request, 'comments/partials/reply_form.html', {
        'form': form,
        'post': post,
        'parent_comment': parent_comment
    })


@login_required
def comment_edit(request, comment_id):
    """
    Редактирование комментария.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Только автор может редактировать
    if comment.author != request.user:
        return HttpResponseForbidden('Вы можете редактировать только свои комментарии.')
    
    if request.method == 'POST':
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.edited_at = timezone.now()
            comment.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'comments/partials/comment.html', {
                    'comment': comment,
                    'user': request.user,
                    'post': comment.post
                })
            
            messages.success(request, 'Комментарий обновлён.')
            return redirect('posts:detail',
                          community_slug=comment.post.community.slug,
                          post_id=comment.post.id,
                          post_slug=comment.post.slug)
    
    # GET — форма редактирования
    form = CommentEditForm(instance=comment)
    
    if request.headers.get('HX-Request'):
        return render(request, 'comments/partials/edit_form.html', {
            'form': form,
            'comment': comment
        })
    
    return render(request, 'comments/edit.html', {
        'form': form,
        'comment': comment
    })


@login_required
def comment_delete(request, comment_id):
    """
    Мягкое удаление комментария (помечаем is_deleted).
    """
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Автор или модератор/админ
    is_moderator = comment.post.community.members.filter(
        user=request.user,
        role__in=['moderator', 'admin']
    ).exists()
    
    if comment.author != request.user and not is_moderator and not request.user.is_staff:
        return HttpResponseForbidden('Нет прав для удаления.')
    
    comment.is_deleted = True
    comment.content = '[удалено]'
    comment.save()
    
    # Обновляем счётчик
    post = comment.post
    post.comment_count = post.comments.filter(is_deleted=False).count()
    post.save()
    
    if request.headers.get('HX-Request'):
        return render(request, 'comments/partials/comment.html', {
            'comment': comment,
            'user': request.user,
            'post': post
        })
    
    messages.success(request, 'Комментарий удалён.')
    return redirect('posts:detail',
                  community_slug=post.community.slug,
                  post_id=post.id,
                  post_slug=post.slug)