from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import User, DanceStyle, Hall, Teacher, ClassSchedule, SubscriptionTariff, Booking, UserSubscription


def home_view(request):
    """
    Главная страница студии 1MILLION.
    Выводит УТП, счетчики залов/педагогов, активные направления и залы студии.
    """
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
    """Каталог расписания (заготовка под Занятие 8)"""
    return HttpResponse("Раздел Расписание занятий (Занятие 8)")


def styles_view(request):
    """Каталог танцевальных стилей (заготовка под Занятие 8)"""
    return HttpResponse("Раздел Каталог направлений (Занятие 8)")


def tariffs_view(request):
    """Тарифная сетка абонементов (заготовка под Занятие 8)"""
    return HttpResponse("Раздел Тарифы и абонементы (Занятие 8)")


def profile_view(request):
    """Личный кабинет ученика (заготовка под Занятие 8)"""
    return HttpResponse("Раздел Личный кабинет ученика (Занятие 8)")


def journal_view(request):
    """Электронный журнал преподавателя (заготовка под Занятие 8)"""
    return HttpResponse("Раздел Журнал преподавателя (Занятие 8)")


def booking_view(request, schedule_id):
    """Форма онлайн-бронирования (заготовка под Занятие 8-9)"""
    return HttpResponse(f"Раздел Бронирование слота #{schedule_id} (Занятие 8-9)")
