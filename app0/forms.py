from django import forms
from django.core.exceptions import ValidationError
from .models import DanceStyle, User


class BookingForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        label='Имя и фамилия',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например, Анна С.'})
    )
    phone = forms.CharField(
        max_length=20,
        label='Номер телефона',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (900) 000-00-00', 'type': 'tel'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('subscription', 'Списать занятие с действующего абонемента'),
            ('single', 'Оплатить разовое занятие в студии (800 ₽)'),
        ],
        label='Способ оплаты',
        widget=forms.RadioSelect(attrs={'class': 'payment-radio-input'})
    )
    agree_rules = forms.BooleanField(
        required=True,
        label='Я подтверждаю бронирование места в зале',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )


class UserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите логин', 'autofocus': True})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'})
    )


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=60,
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ваше имя'})
    )
    last_name = forms.CharField(
        max_length=60,
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ваша фамилия'})
    )
    username = forms.CharField(
        max_length=150,
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Придумайте логин'})
    )
    phone = forms.CharField(
        max_length=20,
        label='Номер телефона',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (900) 000-00-00', 'type': 'tel'})
    )
    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Не менее 6 символов'})
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Повторите пароль'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают.')
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role='student'
        )
