from django.db import models
from django.contrib.auth.models import AbstractUser


# Модель пользователя
class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    role = models.CharField(max_length=20, default='student', verbose_name="Роль в системе")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.get_full_name() or self.username


# Танцевальные направления (стили)
class DanceStyle(models.Model):
    DIFFICULTY_CHOICES = [
        ('all', 'Для всех уровней'),
        ('beginner', 'Начинающий'),
        ('intermediate', 'Продолжающий'),
        ('advanced', 'Продвинутый'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name="Название стиля")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-идентификатор")
    description = models.TextField(blank=True, verbose_name="Описание направления")
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all', verbose_name="Уровень сложности")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Танцевальное направление"
        verbose_name_plural = "Танцевальные направления"

    def __str__(self):
        return self.name


# Залы студии
class Hall(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название зала")
    capacity = models.PositiveSmallIntegerField(default=15, verbose_name="Вместимость (человек)")
    area_sqm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="Площадь (кв. м)")
    has_mirrors = models.BooleanField(default=True, verbose_name="Зеркала")
    has_sound_system = models.BooleanField(default=True, verbose_name="Профессиональный звук")
    description = models.TextField(blank=True, verbose_name="Оснащение и примечания")

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"

    def __str__(self):
        return f"{self.name} (до {self.capacity} чел.)"


# Преподаватели (хореографы)
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile', verbose_name="Пользователь")
    bio = models.TextField(blank=True, verbose_name="О преподавателе")
    experience_years = models.PositiveSmallIntegerField(default=1, verbose_name="Стаж (лет)")
    specialties = models.ManyToManyField(DanceStyle, blank=True, verbose_name="Специализации")
    is_active = models.BooleanField(default=True, verbose_name="Ведет занятия")

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# Тарифы абонементов
class SubscriptionTariff(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название тарифа")
    classes_count = models.PositiveSmallIntegerField(verbose_name="Количество занятий")
    validity_days = models.PositiveSmallIntegerField(default=30, verbose_name="Срок действия (дней)")
    price_rub = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Стоимость (руб.)")
    is_unlimited = models.BooleanField(default=False, verbose_name="Безлимит")
    is_active = models.BooleanField(default=True, verbose_name="Доступен к покупке")
    description = models.TextField(blank=True, verbose_name="Условия тарифа")

    class Meta:
        verbose_name = "Тариф абонемента"
        verbose_name_plural = "Тарифы абонементов"

    def __str__(self):
        return f"{self.name} - {self.price_rub:.0f} руб."


# Абонементы учеников
class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Ученик")
    tariff = models.ForeignKey(SubscriptionTariff, on_delete=models.CASCADE, verbose_name="Тариф")
    purchase_date = models.DateField(auto_now_add=True, verbose_name="Дата оформления")
    start_date = models.DateField(verbose_name="Дата активации")
    end_date = models.DateField(verbose_name="Дата окончания")
    remaining_classes = models.PositiveSmallIntegerField(verbose_name="Остаток занятий")
    status = models.CharField(max_length=20, default='active', verbose_name="Статус")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Примечание")

    class Meta:
        verbose_name = "Абонемент ученика"
        verbose_name_plural = "Абонементы учеников"

    def __str__(self):
        return f"{self.tariff.name} ({self.user})"


# Расписание занятий
class ClassSchedule(models.Model):
    style = models.ForeignKey(DanceStyle, on_delete=models.CASCADE, verbose_name="Направление")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, verbose_name="Зал")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    capacity_limit = models.PositiveSmallIntegerField(default=15, verbose_name="Лимит мест")
    is_canceled = models.BooleanField(default=False, verbose_name="Отменено")
    students = models.ManyToManyField(User, through='Booking', related_name='enrolled_classes')

    class Meta:
        verbose_name = "Занятие в расписании"
        verbose_name_plural = "Расписание занятий"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time} | {self.style.name} | {self.hall.name}"


# Записи (бронирования) на занятия
class Booking(models.Model):
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name='bookings', verbose_name="Занятие")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name="Ученик")
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Абонемент")
    booking_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время записи")
    status = models.CharField(max_length=25, default='booked', verbose_name="Статус")
    is_deducted = models.BooleanField(default=True, verbose_name="Списано")
    cancellation_timestamp = models.DateTimeField(null=True, blank=True, verbose_name="Время отмены")

    class Meta:
        verbose_name = "Запись на занятие"
        verbose_name_plural = "Записи на занятия"
        ordering = ['-booking_timestamp']

    def __str__(self):
        return f"Запись #{self.id}: {self.user} на {self.schedule.style.name}"
