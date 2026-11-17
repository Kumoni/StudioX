from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    User, DanceStyle, Hall, Teacher, ClassSchedule,
    SubscriptionTariff, Booking, UserSubscription
)


def home_view(request):
    """Главная страница студии X."""
    styles = DanceStyle.objects.filter(is_active=True).order_by('name')[:6]
    halls = Hall.objects.all().order_by('name')
    stats = {
        'halls_count': Hall.objects.count(),
        'teachers_count': Teacher.objects.count() or 18,
        'students_count': User.objects.filter(role='student').count() or 1200,
        'styles_count': DanceStyle.objects.filter(is_active=True).count(),
    }
    context = {
        'styles': styles,
        'halls': halls,
        'stats': stats,
    }
    return render(request, 'core/index.html', context)


def schedule_view(request):
    """
    Интерактивное расписание занятий.
    Поддерживает фильтрацию по дням недели, залам, стилям, уровням и преподавателям.
    Пагинация строго по 20 записей.
    """
    # 7 дней недели для переключателя (17 - 23 ноября 2026)
    base_monday = date(2026, 11, 17)
    week_days = []
    ru_day_names = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
    ru_months = ['', 'ЯНВАРЯ', 'ФЕВРАЛЯ', 'МАРТА', 'АПРЕЛЯ', 'МАЯ', 'ИЮНЯ', 'ИЮЛЯ', 'АВГУСТА', 'СЕНТЯБРЯ', 'ОКТЯБРЯ', 'НОЯБРЯ', 'ДЕКАБРЯ']

    for i in range(7):
        cur_d = base_monday + timedelta(days=i)
        week_days.append({
            'date_str': cur_d.strftime('%Y-%m-%d'),
            'day_name': ru_day_names[i],
            'day_num': cur_d.day,
            'month_name': ru_months[cur_d.month],
            'short_name': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'][i],
        })

    # Базовый QuerySet
    queryset = ClassSchedule.objects.select_related(
        'style', 'hall', 'teacher__user', 'replacement_teacher__user'
    ).annotate(
        active_bookings_count=Count(
            'bookings',
            filter=Q(bookings__status__in=['booked', 'attended'])
        )
    ).order_by('date', 'start_time')

    # Получение GET-фильтров
    selected_date = request.GET.get('date', '')
    selected_hall = request.GET.get('hall', '')
    selected_style = request.GET.get('style', '')
    selected_difficulty = request.GET.get('difficulty', '')
    selected_teacher = request.GET.get('teacher', '')

    if selected_date:
        queryset = queryset.filter(date=selected_date)
    if selected_hall:
        queryset = queryset.filter(hall_id=selected_hall)
    if selected_style:
        queryset = queryset.filter(style_id=selected_style)
    if selected_difficulty:
        queryset = queryset.filter(style__difficulty_level=selected_difficulty)
    if selected_teacher:
        queryset = queryset.filter(Q(teacher_id=selected_teacher) | Q(replacement_teacher_id=selected_teacher))

    # Вычисление свободных мест для каждого слота
    slots = list(queryset)
    for slot in slots:
        slot.free_spots = max(0, slot.capacity_limit - slot.active_bookings_count)
        # Вычисление длительности в минутах
        slot.duration_minutes = (slot.end_time.hour * 60 + slot.end_time.minute) - (slot.start_time.hour * 60 + slot.start_time.minute)

    # Пагинация по 20 записей (требование ТЗ Занятия 8)
    paginator = Paginator(slots, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Справочники для селекторов
    halls = Hall.objects.all().order_by('name')
    styles = DanceStyle.objects.filter(is_active=True).order_by('name')
    teachers = Teacher.objects.filter(is_active=True).select_related('user').order_by('user__last_name')
    difficulty_choices = DanceStyle.DIFFICULTY_CHOICES

    context = {
        'week_days': week_days,
        'selected_date': selected_date,
        'selected_hall': selected_hall,
        'selected_style': selected_style,
        'selected_difficulty': selected_difficulty,
        'selected_teacher': selected_teacher,
        'page_obj': page_obj,
        'halls': halls,
        'styles': styles,
        'teachers': teachers,
        'difficulty_choices': difficulty_choices,
        'total_slots_count': len(slots),
    }
    return render(request, 'core/schedule.html', context)


def tariffs_view(request):
    """
    Тарифная сетка абонементов по макету Тарифы.png.
    """
    tariffs = list(SubscriptionTariff.objects.filter(is_active=True).order_by('price_rub'))
    for tariff in tariffs:
        if not tariff.is_unlimited and tariff.classes_count:
            tariff.per_lesson = int(tariff.price_rub / tariff.classes_count)
        else:
            tariff.per_lesson = None
        # По макету Figma Тарифы.png хит продаж — абонемент на 8 занятий
        tariff.is_hit = (tariff.classes_count == 8)

    context = {
        'tariffs': tariffs,
    }
    return render(request, 'core/tariffs.html', context)


def styles_view(request):
    """Каталог танцевальных стилей (заготовка под Занятие 8 шаг 3)"""
    return HttpResponse("Каталог стилей")


def profile_view(request):
    """Личный кабинет ученика (заготовка под Занятие 8 шаг 2)"""
    return HttpResponse("Личный кабинет ученика")


def journal_view(request):
    """Электронный журнал преподавателя (заготовка под Занятие 8 шаг 2)"""
    return HttpResponse("Журнал преподавателя")


def booking_view(request, schedule_id):
    """Форма онлайн-бронирования (заготовка под Занятие 8 шаг 3)"""
    return HttpResponse(f"Бронирование слота #{schedule_id}")
