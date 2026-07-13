from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import UserProfile

# Получаем модель пользователя (нашу кастомную User)
User = get_user_model()


class RegisterForm(UserCreationForm):
    """
    Форма регистрации нового пользователя.
    Наследуемся от UserCreationForm — Django уже сделал проверку паролей,
    хеширование и другие сложные вещи.
    """
    # Добавляем поле email (по умолчанию его нет в UserCreationForm)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent',
            'placeholder': 'your@email.com'
        }),
        label='Email'
    )
    
    class Meta:
        model = User  # Используем нашу кастомную модель User
        fields = ['username', 'email', 'password1', 'password2']
        # password1 — пароль, password2 — подтверждение пароля
    
    def __init__(self, *args, **kwargs):
        """
        Переопределяем конструктор, чтобы добавить CSS-классы ко всем полям.
        Это нужно для стилизации Tailwind.
        """
        super().__init__(*args, **kwargs)
        
        # Стили для всех полей
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors'
            })
        
        # Плейсхолдеры для полей
        self.fields['username'].widget.attrs['placeholder'] = 'Придумайте никнейм'
        self.fields['password1'].widget.attrs['placeholder'] = 'Придумайте пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'
        
        # Убираем стандартные подсказки Django (они длинные и на английском)
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
    
    def clean_email(self):
        """
        Проверка уникальности email.
        Метод clean_ИМЯПОЛЯ вызывается автоматически при валидации.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже зарегистрирован.')
        return email
    
    def clean_username(self):
        """
        Проверка: никнейм должен содержать только буквы, цифры и подчёркивание.
        """
        username = self.cleaned_data.get('username')
        if not username.replace('_', '').isalnum():
            raise forms.ValidationError('Никнейм может содержать только буквы, цифры и подчёркивание.')
        if len(username) < 3:
            raise forms.ValidationError('Никнейм должен быть не короче 3 символов.')
        return username


class LoginForm(AuthenticationForm):
    """
    Форма входа (логина).
    Наследуемся от AuthenticationForm — Django проверяет логин/пароль автоматически.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Стилизация полей Tailwind
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors'
            })
        
        self.fields['username'].widget.attrs['placeholder'] = 'Никнейм или email'
        self.fields['password'].widget.attrs['placeholder'] = 'Пароль'


class ProfileEditForm(forms.ModelForm):
    """
    Форма редактирования профиля.
    ModelForm автоматически создаёт поля на основе модели.
    """
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'show_email', 'nsfw_enabled']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500'
            }),
            'show_email': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-500 rounded focus:ring-orange-500'
            }),
            'nsfw_enabled': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-500 rounded focus:ring-orange-500'
            }),
        }
        labels = {
            'avatar': 'Аватар',
            'bio': 'О себе',
            'show_email': 'Показывать email в профиле',
            'nsfw_enabled': 'Показывать NSFW-контент'
        }