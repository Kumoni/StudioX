from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date, timedelta

from .models import (
    User, DanceStyle, Hall, Teacher, ClassSchedule,
    SubscriptionTariff, Booking, UserSubscription
)
from .forms import BookingForm, UserLoginForm, UserRegistrationForm


# Главная страница
def home_view(request):
    styles = DanceStyle.objects.filter(is_active=True)[:6]
    halls = Hall.objects.all()
    stats = {
        'halls_count': halls.count(),
        'teachers_count': Teacher.objects.count() or 18,
        'students_count': User.objects.count() or 1200,
        'styles_count': DanceStyle.objects.count(),
    }
    return render(request, 'index.html', {
        'styles': styles,
        'halls': halls,
        'stats': stats,
    })


# Расписание занятий
def schedule_view(request):
    base_monday = date(2026, 11, 17)
    week_days = []
    day_names = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
    months = ['', 'ЯНВАРЯ', 'ФЕВРАЛЯ', 'МАРТА', 'АПРЕЛЯ', 'МАЯ', 'ИЮНЯ', 'ИЮЛЯ', 'АВГУСТА', 'СЕНТЯБРЯ', 'ОКТЯБРЯ', 'НОЯБРЯ', 'ДЕКАБРЯ']

    for i in range(7):
        cur_d = base_monday + timedelta(days=i)
        week_days.append({
            'date_str': cur_d.strftime('%Y-%m-%d'),
            'day_name': day_names[i],
            'day_num': cur_d.day,
            'month_name': months[cur_d.month],
            'short_name': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'][i],
        })

    slots = ClassSchedule.objects.all().order_by('date', 'start_time')

    selected_date = request.GET.get('date', '')
    selected_hall = request.GET.get('hall', '')
    selected_style = request.GET.get('style', '')
    selected_difficulty = request.GET.get('difficulty', '')
    selected_teacher = request.GET.get('teacher', '')

    if selected_date:
        slots = slots.filter(date=selected_date)
    if selected_hall:
        slots = slots.filter(hall_id=selected_hall)
    if selected_style:
        slots = slots.filter(style_id=selected_style)
    if selected_difficulty:
        slots = slots.filter(style__difficulty_level=selected_difficulty)
    if selected_teacher:
        slots = slots.filter(teacher_id=selected_teacher)

    slots_list = list(slots)
    for slot in slots_list:
        booked = slot.bookings.count()
        slot.free_spots = max(0, slot.capacity_limit - booked)
        slot.duration_minutes = 90

    return render(request, 'schedule.html', {
        'week_days': week_days,
        'selected_date': selected_date,
        'selected_hall': selected_hall,
        'selected_style': selected_style,
        'selected_difficulty': selected_difficulty,
        'selected_teacher': selected_teacher,
        'page_obj': slots_list,
        'halls': Hall.objects.all(),
        'styles': DanceStyle.objects.filter(is_active=True),
        'teachers': Teacher.objects.all(),
        'difficulty_choices': DanceStyle.DIFFICULTY_CHOICES,
        'total_slots_count': len(slots_list),
    })


# Тарифы и абонементы
def tariffs_view(request):
    tariffs = SubscriptionTariff.objects.filter(is_active=True).order_by('price_rub')
    return render(request, 'tariffs.html', {'tariffs': tariffs})


# Каталог направлений
def styles_view(request):
    query = request.GET.get('q', '').strip()
    difficulty = request.GET.get('difficulty', '')

    styles = DanceStyle.objects.filter(is_active=True)
    if query:
        styles = styles.filter(name__icontains=query)
    if difficulty:
        styles = styles.filter(difficulty_level=difficulty)

    return render(request, 'styles.html', {
        'styles': styles,
        'teachers': Teacher.objects.all(),
        'difficulty_choices': DanceStyle.DIFFICULTY_CHOICES,
        'selected_difficulty': difficulty,
        'query': query,
    })


# Личный кабинет
def profile_view(request):
    student = request.user if request.user.is_authenticated else User.objects.first()

    current_sub = student.subscriptions.filter(status='active').first() if student else None
    if current_sub and current_sub.tariff.classes_count:
        current_sub.progress_pct = int((current_sub.remaining_classes / current_sub.tariff.classes_count) * 100)
        current_sub.used_classes = current_sub.tariff.classes_count - current_sub.remaining_classes

    upcoming_bookings = student.bookings.all().order_by('-booking_timestamp') if student else []

    return render(request, 'profile.html', {
        'student': student,
        'current_sub': current_sub,
        'upcoming_bookings': upcoming_bookings,
    })


# Запись на занятие
def booking_view(request, schedule_id):
    slot = get_object_or_404(ClassSchedule, id=schedule_id)
    student = request.user if request.user.is_authenticated else User.objects.first()

    booked_count = slot.bookings.count()
    free_spots = max(0, slot.capacity_limit - booked_count)
    slot.free_spots = free_spots

    active_sub = student.subscriptions.filter(status='active', remaining_classes__gt=0).first() if student else None

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            if Booking.objects.filter(schedule=slot, user=student).exists():
                messages.warning(request, 'Вы уже записаны на это занятие.')
                return redirect('profile')

            payment_method = form.cleaned_data['payment_method']
            used_sub = active_sub if payment_method == 'subscription' else None
            if used_sub:
                used_sub.remaining_classes = max(0, used_sub.remaining_classes - 1)
                used_sub.save()

            Booking.objects.create(
                schedule=slot,
                user=student,
                subscription=used_sub,
                status='booked'
            )
            messages.success(request, f'Вы успешно записаны на {slot.style.name}!')
            return redirect('profile')
    else:
        form = BookingForm(initial={
            'full_name': student.get_full_name() or student.username,
            'phone': student.phone,
        })

    return render(request, 'booking_detail.html', {
        'slot': slot,
        'student': student,
        'active_sub': active_sub,
        'free_spots': free_spots,
        'form': form,
    })


# Отмена записи на занятие
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.subscription:
        booking.subscription.remaining_classes += 1
        booking.subscription.save()

    booking.delete()
    messages.success(request, 'Запись на занятие успешно отменена.')
    return redirect('profile')


# Авторизация (вход)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('profile')
            messages.error(request, 'Неверный логин или пароль.')
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


# Регистрация
def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


# Выход из системы
def logout_view(request):
    logout(request)
    return redirect('home')
