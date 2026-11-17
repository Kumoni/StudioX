from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    
    path('schedule/', views.schedule_view, name='schedule'),
    path('shedule/', views.schedule_view),
    
    path('styles/', views.styles_view, name='styles'),
    
    path('tariffs/', views.tariffs_view, name='tariffs'),
    
    path('profile/', views.profile_view, name='profile'),
    
    path('journal/', views.journal_view, name='journal'),
    
    path('booking/<int:schedule_id>/', views.booking_view, name='booking'),
]
