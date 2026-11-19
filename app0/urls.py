from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('tariffs/', views.tariffs_view, name='tariffs'),
    path('styles/', views.styles_view, name='styles'),
    path('profile/', views.profile_view, name='profile'),
    path('booking/<int:schedule_id>/', views.booking_view, name='booking'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
