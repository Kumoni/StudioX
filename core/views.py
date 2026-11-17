from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, date, timedelta
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
    """
    Личный кабинет ученика по макету ЛичныйКабинет.png:
    - Персональные данные и статус ученика
    - Карточка активного абонемента с остатком и шкалой прогресса
    - Таблица активных броней с проверкой правила отмены за 2 часа
    - История посещенных занятий со статусами списания
    """
    user_id = request.GET.get('user_id', 6)
    try:
        student = User.objects.get(id=user_id)
    except User.DoesNotExist:
        student = User.objects.filter(role='student').first()

    # Активные абонементы
    active_subscriptions = student.subscriptions.filter(status='active').select_related('tariff').order_by('-start_date')
    current_sub = active_subscriptions.first()

    if current_sub and current_sub.tariff.classes_count:
        current_sub.progress_pct = int((current_sub.remaining_classes / current_sub.tariff.classes_count) * 100)
        current_sub.used_classes = max(0, current_sub.tariff.classes_count - current_sub.remaining_classes)
    elif current_sub:
        current_sub.progress_pct = 100
        current_sub.used_classes = 0

    # Бронирования: предстоящие и история
    all_bookings = student.bookings.select_related(
        'schedule__style', 'schedule__hall', 'schedule__teacher__user', 'subscription__tariff'
    ).order_by('schedule__date', 'schedule__start_time')

    now_dt = datetime(2026, 11, 17, 12, 0)

    upcoming_bookings = []
    history_bookings = []

    for b in all_bookings:
        slot_dt = datetime.combine(b.schedule.date, b.schedule.start_time)
        diff_hours = (slot_dt - now_dt).total_seconds() / 3600.0
        b.can_cancel = (diff_hours >= 2.0)
        b.hours_left = max(0, round(diff_hours, 1))

        if b.status == 'booked' and slot_dt >= now_dt:
            upcoming_bookings.append(b)
        else:
            history_bookings.append(b)

    history_bookings.reverse()

    context = {
        'student': student,
        'current_sub': current_sub,
        'active_subscriptions': active_subscriptions,
        'upcoming_bookings': upcoming_bookings,
        'history_bookings': history_bookings,
        'now_dt': now_dt,
    }
    return render(request, 'core/profile.html', context)


def journal_view(request):
    """
    Электронный журнал преподавателя по макету ЖурналПреподавателя.png:
    - Выбор слота расписания преподавателя
    - Сводка заполняемости и посещаемости группы
    - Список записанных студентов с переключателями статуса (Присутствовал / Пропуск)
    """
    teacher_id = request.GET.get('teacher_id')
    if teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
    else:
        teacher = Teacher.objects.filter(user__username='t_elena').first() or Teacher.objects.first()

    # Все слоты преподавателя
    teacher_slots = ClassSchedule.objects.filter(
        Q(teacher=teacher) | Q(replacement_teacher=teacher)
    ).select_related('style', 'hall').order_by('-date', '-start_time')

    # Выбранный слот
    slot_id = request.GET.get('slot_id')
    if slot_id:
        current_slot = get_object_or_404(ClassSchedule, id=slot_id)
    else:
        current_slot = teacher_slots.annotate(cnt=Count('bookings')).order_by('-cnt').first()

    # Записи учеников на текущий слот
    bookings = []
    stats = {'total': 0, 'attended': 0, 'missed': 0, 'booked': 0, 'rate': 0}
    if current_slot:
        bookings = list(current_slot.bookings.select_related(
            'user', 'subscription__tariff'
        ).order_by('user__last_name', 'user__first_name'))

        stats['total'] = len(bookings)
        stats['attended'] = sum(1 for b in bookings if b.status == 'attended')
        stats['missed'] = sum(1 for b in bookings if b.status in ['missed', 'canceled_penalty'])
        stats['booked'] = sum(1 for b in bookings if b.status == 'booked')
        if stats['total'] > 0:
            stats['rate'] = int((stats['attended'] / stats['total']) * 100)

    all_teachers = Teacher.objects.filter(is_active=True).select_related('user')

    context = {
        'teacher': teacher,
        'all_teachers': all_teachers,
        'teacher_slots': teacher_slots,
        'current_slot': current_slot,
        'bookings': bookings,
        'stats': stats,
    }
    return render(request, 'core/journal.html', context)


def booking_view(request, schedule_id):
    """Форма онлайн-бронирования (заготовка под Занятие 8 шаг 3)"""
    return HttpResponse(f"Бронирование слота #{schedule_id}")
