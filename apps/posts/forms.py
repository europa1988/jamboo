from django import forms
from django.db import models
from slugify import slugify
from .models import Post
from apps.communities.models import Community

class PostCreateForm(forms.ModelForm):
    """
    Форма создания поста.
    ModelForm автоматически создаёт поля на основе модели Post.
    """
    
    # Переопределяем поле community, чтобы показывать только сообщества,
    # в которых пользователь является участником (или все, если создатель)
    community = forms.ModelChoiceField(
        queryset=Community.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white'
        }),
        label='Сообщество',
        empty_label='Выберите сообщество'
    )
    
    class Meta:
        model = Post
        fields = ['title', 'post_type', 'content', 'url', 'image', 'community', 'is_nsfw', 'is_spoiler']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'placeholder': 'Заголовок поста',
                'maxlength': '300'
            }),
            'post_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-y',
                'placeholder': 'Текст поста...',
                'rows': 6
            }),
            'url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'placeholder': 'https://example.com'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100'
            }),
            'is_nsfw': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-500 rounded focus:ring-orange-500 border-gray-300'
            }),
            'is_spoiler': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-500 rounded focus:ring-orange-500 border-gray-300'
            }),
        }
        labels = {
            'title': 'Заголовок',
            'post_type': 'Тип поста',
            'content': 'Текст',
            'url': 'Ссылка',
            'image': 'Изображение',
            'is_nsfw': 'NSFW (18+)',
            'is_spoiler': 'Спойлер'
        }
    
    def __init__(self, *args, user=None, **kwargs):
        """
        user передаётся из view, чтобы фильтровать сообщества.
        """
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Если пользователь передан — фильтруем сообщества
        if self.user:
            # Показываем сообщества, где пользователь участник или создатель
            self.fields['community'].queryset = Community.objects.filter(
                models.Q(members__user=self.user) | models.Q(creator=self.user)
            ).distinct()
    
    def clean_title(self):
        """
        Проверка заголовка.
        """
        title = self.cleaned_data.get('title')
        if len(title.strip()) < 5:
            raise forms.ValidationError('Заголовок должен быть не короче 5 символов.')
        return title.strip()
    
    def clean(self):
        """
        Совместная проверка полей.
        """
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        content = cleaned_data.get('content')
        url = cleaned_data.get('url')
        image = cleaned_data.get('image')
        
        # Проверка в зависимости от типа поста
        if post_type == 'text' and not content:
            self.add_error('content', 'Текстовый пост должен содержать текст.')
        
        if post_type == 'link' and not url:
            self.add_error('url', 'Укажите ссылку.')
        
        if post_type == 'image' and not image:
            self.add_error('image', 'Загрузите изображение.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Переопределяем save для автоматического создания slug.
        """
        instance = super().save(commit=False)
        
        # Автоматически генерируем slug из заголовка
        base_slug = slugify(instance.title, max_length=50)
        slug = base_slug
        counter = 1
        
        # Проверяем уникальность slug
        while Post.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug
        
        # Автор — текущий пользователь
        instance.author = self.user
        
        if commit:
            instance.save()
        
        return instance