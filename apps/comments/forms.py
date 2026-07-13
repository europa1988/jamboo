from django import forms
from .models import Comment


class CommentCreateForm(forms.ModelForm):
    """
    Форма создания комментария.
    """
    # Скрытое поле для parent_id (ответ на комментарий)
    parent_id = forms.IntegerField(
        widget=forms.HiddenInput,
        required=False
    )
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-y',
                'rows': 3,
                'placeholder': 'Что вы думаете?'
            })
        }
        labels = {
            'content': ''
        }
    
    def clean_content(self):
        """
        Проверка содержимого комментария.
        """
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 2:
            raise forms.ValidationError('Комментарий слишком короткий.')
        if len(content) > 5000:
            raise forms.ValidationError('Комментарий не может быть длиннее 5000 символов.')
        return content


class CommentEditForm(forms.ModelForm):
    """
    Форма редактирования комментария.
    """
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-y',
                'rows': 3
            })
        }
        labels = {
            'content': ''
        }