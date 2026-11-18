from django import forms
from django.core.exceptions import ValidationError
from datetime import date
import re
from .models import DanceStyle, UserSubscription, Booking, ClassSchedule


class BookingForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        label='Имя и фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Например, Мария Иванова',
            'required': True,
        })
    )
    phone = forms.CharField(
        max_length=20,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+7 (999) 000-00-00',
            'type': 'tel',
            'required': True,
        })
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
        label='Я подтверждаю бронирование и ознакомлен(а) с правилом отмены за 2 часа',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    def __init__(self, *args, user=None, slot=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.slot = slot
        if user and not self.is_bound:
            self.fields['full_name'].initial = user.get_full_name() or user.username
            self.fields['phone'].initial = user.phone

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 3:
            raise ValidationError('Имя должно содержать не менее 3 символов.')
        parts = name.split()
        if len(parts) < 2:
            raise ValidationError('Пожалуйста, укажите имя и фамилию через пробел.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) not in (10, 11):
            raise ValidationError('Номер телефона должен содержать 10 или 11 цифр.')
        if len(digits) == 11 and digits[0] not in ('7', '8'):
            raise ValidationError('Некорректный код страны. Номер должен начинаться с +7 или 8.')
        if len(digits) == 10:
            digits = '7' + digits
        formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        return formatted

    def clean(self):
        cleaned_data = super().clean()
        if not self.slot:
            return cleaned_data

        if self.slot.is_canceled:
            raise ValidationError('Занятие отменено администрацией студии.')

        active_count = self.slot.bookings.filter(status__in=['booked', 'attended']).count()
        if active_count >= self.slot.capacity_limit:
            raise ValidationError('К сожалению, в группе больше нет свободных мест.')

        payment_method = cleaned_data.get('payment_method')
        if payment_method == 'subscription':
            if not self.user:
                raise ValidationError('Для списания с абонемента требуется профиль ученика.')
            user_subs = self.user.subscriptions.filter(status='active', remaining_classes__gt=0)
            if not user_subs.exists():
                raise ValidationError('У вас нет активного абонемента с доступными занятиями. Выберите разовую оплату.')

        return cleaned_data


class SubscriptionFreezeForm(forms.Form):
    start_date = forms.DateField(
        label='Дата начала заморозки',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input',
            'required': True,
        })
    )
    days = forms.ChoiceField(
        choices=[('7', '7 календарных дней'), ('14', '14 календарных дней')],
        label='Длительность заморозки',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        max_length=200,
        required=False,
        label='Причина заморозки',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Отпуск, командировка, сессия...'
        })
    )

    def __init__(self, *args, subscription=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscription = subscription

    def clean_start_date(self):
        s_date = self.cleaned_data.get('start_date')
        if s_date and s_date < date.today():
            raise ValidationError('Дата начала заморозки не может быть в прошлом.')
        return s_date

    def clean(self):
        cleaned_data = super().clean()
        days = int(cleaned_data.get('days') or 7)
        if self.subscription:
            tariff = self.subscription.tariff
            if tariff.classes_count < 8 and days > 7:
                raise ValidationError('Для данного тарифа максимальный срок заморозки составляет 7 дней.')
        return cleaned_data


class TrialClassForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Ваше имя',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Иван Иванов',
            'required': True,
        })
    )
    phone = forms.CharField(
        max_length=20,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+7 (999) 000-00-00',
            'type': 'tel',
            'required': True,
        })
    )
    style = forms.ModelChoiceField(
        queryset=DanceStyle.objects.filter(is_active=True),
        label='Интересующее направление',
        empty_label='Выберите стиль танца',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preferred_time = forms.ChoiceField(
        choices=[
            ('morning', 'Утро (10:00 — 14:00)'),
            ('evening', 'Вечер (18:00 — 22:00)'),
            ('weekend', 'Выходные дни'),
        ],
        label='Удобное время',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) not in (10, 11):
            raise ValidationError('Введите корректный номер телефона (10 или 11 цифр).')
        return phone
