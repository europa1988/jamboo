from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.template.loader import render_to_string

from apps.posts.models import Post
from apps.comments.models import Comment
from .models import PostVote, CommentVote


@login_required
def vote_post(request, post_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    action = request.POST.get('action')
    
    if action not in ['up', 'down']:
        return HttpResponseBadRequest('Неверное действие')
    
    value = 1 if action == 'up' else -1
    
    existing_vote = PostVote.objects.filter(user=request.user, post=post).first()
    
    if existing_vote:
        if existing_vote.value == value:
            existing_vote.delete()
        else:
            existing_vote.value = value
            existing_vote.save()
    else:
        PostVote.objects.create(user=request.user, post=post, value=value)
    
    post.update_score()
    post.refresh_from_db()
    
    return render(request, 'votes/partials/post_vote.html', {
        'post': post,
        'user_vote': post.get_user_vote(request.user)
    })


@login_required
def vote_comment(request, comment_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    action = request.POST.get('action')
    
    if action not in ['up', 'down']:
        return HttpResponseBadRequest('Неверное действие')
    
    value = 1 if action == 'up' else -1
    
    existing_vote = CommentVote.objects.filter(user=request.user, comment=comment).first()
    
    if existing_vote:
        if existing_vote.value == value:
            existing_vote.delete()
        else:
            existing_vote.value = value
            existing_vote.save()
    else:
        CommentVote.objects.create(user=request.user, comment=comment, value=value)
    
    comment.update_score()
    comment.refresh_from_db()
    
    return render(request, 'votes/partials/comment_vote.html', {
        'comment': comment,
        'user_vote': comment.get_user_vote(request.user)
    })