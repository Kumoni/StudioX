from django.contrib import admin
from .models import (
    User, DanceStyle, Hall, Teacher,
    SubscriptionTariff, UserSubscription, ClassSchedule, Booking
)

admin.site.register(User)
admin.site.register(DanceStyle)
admin.site.register(Hall)
admin.site.register(Teacher)
admin.site.register(SubscriptionTariff)
admin.site.register(UserSubscription)
admin.site.register(ClassSchedule)
admin.site.register(Booking)
