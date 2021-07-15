from django.contrib import admin
from .models import User, Subscription, UserSubscription

# Register your models here.
admin.site.register(User)
admin.site.register(Subscription)
admin.site.register(UserSubscription)
