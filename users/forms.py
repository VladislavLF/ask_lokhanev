from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from app.models import Profile, Answer, Question, Tag
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Введите логин',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password'
        }),
        strip=False
    )

    error_messages = {
        'invalid_login': "Неверные учетные данные. Попробуйте снова.",
        'inactive': "Этот аккаунт неактивен.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'aria-describedby': 'usernameHelp'})
        self.fields['password'].widget.attrs.update({'aria-describedby': 'passwordHelp'})

class RegisterUserForm(forms.ModelForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Введите логин'
        }),
        help_text="Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_."
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Введите email'
        })
    )
    name = forms.CharField(
        label="Псевдоним",
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Введите псевдоним'
        }),
        help_text="Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_."
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Введите пароль'
        }),
        help_text="Пароль должен содержать не менее 8 символов."
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control mb-2',
            'placeholder': 'Повторите пароль'
        })
    )
    avatar = forms.ImageField(
        label="Аватар",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control mb-2'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()  # Нормализация email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        try:
            validate_password(password1)  # Проверка сложности пароля
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            avatar = self.cleaned_data.get('avatar')
            if avatar == None:
                avatar = 'avatars/default.png'
            Profile.objects.create(
                user=user,
                name=self.cleaned_data.get('name'),
                avatar=avatar
            )
        return user


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={
        'class': 'form-control mb-2',
        'placeholder': 'Введите логин'
    }))
    email = forms.EmailField(label="Электронная почта", widget=forms.EmailInput(attrs={
        'class': 'form-control mb-2',
        'placeholder': 'Введите электронную почту'
    }))
    name = forms.CharField(label="Псевдоним", widget=forms.TextInput(attrs={
        'class': 'form-control mb-2',
        'placeholder': 'Введите псевдоним'
    }))
    avatar = forms.ImageField(
        label="Аватар",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control mb-2'
        })
    )

    class Meta:
        model = Profile
        fields = ['username', 'email', 'name', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.email = self.cleaned_data['email']
        profile.user.username = self.cleaned_data['username']
        profile.name = self.cleaned_data['name']
        profile.avatar = self.cleaned_data['avatar']
        if commit:
            profile.user.save()
            profile.save()
        return profile

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Введите ваш ответ...',
                'id': 'answer-textarea'
            }),
        }
        labels = {
            'text': 'Ваш ответ'
        }
        help_texts = {
            'text': 'Минимум 20 символов, используйте разметку Markdown'
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) < 20:
            raise forms.ValidationError("Ответ должен содержать не менее 20 символов")
        return text


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=200,
        required=False,
        help_text="Введи теги через запятую"
    )

    class Meta:
        model = Question
        fields = ['title', 'text', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }

    def clean_tags(self):
        tags_string = self.cleaned_data['tags']
        tag_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        if len(tag_list) > 3:
            raise forms.ValidationError("Максимум 3 тега.")
        return tag_list
