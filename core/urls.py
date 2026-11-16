from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.home_view, name='home'),
    
    # Расписание занятий
    path('shedule/', views.schedule_view, name='schedule'),
    
    # Каталог стилей
    path('styles/', views.styles_view, name='styles'),
    
    # Тарифы и абонементы
    path('tariffs/', views.tariffs_view, name='tariffs'),
    
    # Личный кабинет ученика
    path('profile/', views.profile_view, name='profile'),
    
    # Журнал преподавателя
    path('journal/', views.journal_view, name='journal'),
    
    # Детальное бронирование
    path('booking/<int:schedule_id>/', views.booking_view, name='booking'),
]
