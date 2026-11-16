from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Гость'),
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]

    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номер телефона",
        help_text="Формат +7XXXXXXXXXX"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name="Роль в системе"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} ({self.get_role_display()})"


class DanceStyle(models.Model):
    DIFFICULTY_CHOICES = [
        ('all', 'Для всех уровней'),
        ('beginner', 'Начинающий'),
        ('intermediate', 'Продолжающий'),
        ('advanced', 'Продвинутый'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название стиля"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL-идентификатор"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание направления"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='all',
        verbose_name="Уровень сложности"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно"
    )

    class Meta:
        verbose_name = "Танцевальное направление"
        verbose_name_plural = "Танцевальные направления"
        ordering = ['name']

    def __str__(self):
        return self.name


class Hall(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название зала"
    )
    capacity = models.PositiveSmallIntegerField(
        verbose_name="Вместимость (человек)"
    )
    area_sqm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Площадь (кв. м)"
    )
    has_mirrors = models.BooleanField(
        default=True,
        verbose_name="Зеркала во всю стену"
    )
    has_sound_system = models.BooleanField(
        default=True,
        verbose_name="Профессиональный звук"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Оснащение и примечания"
    )

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0),
                name='check_hall_capacity_positive'
            ),
        ]

    def __str__(self):
        return f"{self.name} (до {self.capacity} чел.)"


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name="Учетная запись"
    )
    bio = models.TextField(
        verbose_name="О преподавателе"
    )
    experience_years = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Стаж (лет)"
    )
    specialties = models.ManyToManyField(
        DanceStyle,
        related_name='teachers',
        blank=True,
        verbose_name="Специализации"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ведет занятия"
    )

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ['user__last_name', 'user__first_name']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(experience_years__gte=0),
                name='check_teacher_experience_non_negative'
            ),
        ]

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} (стаж: {self.experience_years} г.)"


class SubscriptionTariff(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название тарифа"
    )
    classes_count = models.PositiveSmallIntegerField(
        verbose_name="Количество занятий"
    )
    validity_days = models.PositiveSmallIntegerField(
        verbose_name="Срок действия (дней)"
    )
    price_rub = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Стоимость (руб.)"
    )
    is_unlimited = models.BooleanField(
        default=False,
        verbose_name="Безлимит"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Доступен к покупке"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Условия тарифа"
    )

    class Meta:
        verbose_name = "Тариф абонемента"
        verbose_name_plural = "Тарифы абонементов"
        ordering = ['price_rub']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price_rub__gte=0),
                name='check_tariff_price_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(validity_days__gt=0),
                name='check_tariff_validity_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(classes_count__gt=0),
                name='check_tariff_classes_positive'
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.price_rub:.0f} руб."


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('expired', 'Истек срок'),
        ('exhausted', 'Занятия исчерпаны'),
        ('frozen', 'Заморожен'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Ученик"
    )
    tariff = models.ForeignKey(
        SubscriptionTariff,
        on_delete=models.PROTECT,
        related_name='issued_subscriptions',
        verbose_name="Тариф"
    )
    purchase_date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата оформления"
    )
    start_date = models.DateField(
        verbose_name="Дата активации"
    )
    end_date = models.DateField(
        verbose_name="Дата окончания"
    )
    remaining_classes = models.PositiveSmallIntegerField(
        verbose_name="Остаток занятий"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус абонемента"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Примечание администратора"
    )

    class Meta:
        verbose_name = "Абонемент ученика"
        verbose_name_plural = "Абонементы учеников"
        ordering = ['-start_date', 'status']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F('start_date')),
                name='check_subscription_end_date_valid'
            ),
            models.CheckConstraint(
                condition=models.Q(remaining_classes__gte=0),
                name='check_subscription_remaining_non_negative'
            ),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username
        return f"Абонемент #{self.pk}: {self.tariff.name} ({user_name})"


class ClassSchedule(models.Model):
    style = models.ForeignKey(
        DanceStyle,
        on_delete=models.PROTECT,
        related_name='scheduled_classes',
        verbose_name="Направление"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='conducted_classes',
        verbose_name="Преподаватель"
    )
    replacement_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='substituted_classes',
        verbose_name="Заменяющий преподаватель"
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.PROTECT,
        related_name='scheduled_classes',
        verbose_name="Зал"
    )
    date = models.DateField(
        verbose_name="Дата занятия"
    )
    start_time = models.TimeField(
        verbose_name="Время начала"
    )
    end_time = models.TimeField(
        verbose_name="Время окончания"
    )
    capacity_limit = models.PositiveSmallIntegerField(
        verbose_name="Лимит мест"
    )
    is_canceled = models.BooleanField(
        default=False,
        verbose_name="Отменено"
    )
    cancellation_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Причина отмены"
    )
    students = models.ManyToManyField(
        User,
        through='Booking',
        related_name='enrolled_classes',
        verbose_name="Записанные ученики"
    )

    class Meta:
        verbose_name = "Занятие в расписании"
        verbose_name_plural = "Расписание занятий"
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['hall', 'date', 'start_time'],
                name='unique_hall_slot_per_time'
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='check_class_end_after_start'
            ),
            models.CheckConstraint(
                condition=models.Q(capacity_limit__gt=0),
                name='check_capacity_limit_positive'
            ),
        ]

    def __str__(self):
        active_teacher = self.replacement_teacher if self.replacement_teacher else self.teacher
        return f"{self.date.strftime('%d.%m.%Y')} {self.start_time.strftime('%H:%M')} | {self.style.name} | {self.hall.name} | {active_teacher}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Записан'),
        ('attended', 'Посетил'),
        ('canceled', 'Отменено клиентом вовремя'),
        ('canceled_penalty', 'Поздняя отмена со списанием'),
        ('missed', 'Неявка со списанием'),
    ]

    schedule = models.ForeignKey(
        ClassSchedule,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Занятие"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Ученик"
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name="Списанный абонемент"
    )
    booking_timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время записи"
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='booked',
        verbose_name="Статус бронирования"
    )
    is_deducted = models.BooleanField(
        default=True,
        verbose_name="Занятие списано"
    )
    cancellation_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время отмены"
    )

    class Meta:
        verbose_name = "Запись на занятие"
        verbose_name_plural = "Записи на занятия"
        ordering = ['-booking_timestamp']
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'user'],
                name='unique_user_booking_per_class'
            ),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username
        return f"Запись #{self.pk}: {user_name} -> {self.schedule.style.name} ({self.schedule.date.strftime('%d.%m.%Y')})"
