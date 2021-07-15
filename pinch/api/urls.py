from django.urls import path
from rest_framework import routers
from . import views

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'subscription', views.SubscriptionViewSet)
router.register(r'bookmark', views.BookmarkViewSet)

urlpatterns = router.urls + [
    path('email', views.email),
    path('user/email-senders', views.email_senders),
]
