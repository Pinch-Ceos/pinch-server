from django.contrib import admin
from .models import User, Subscription, UserSubscription, Bookmark

# Register your models here.
admin.site.register(User)
admin.site.register(Subscription)
admin.site.register(UserSubscription)
admin.site.register(Bookmark)
