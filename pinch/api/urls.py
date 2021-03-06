from django.urls import path
from rest_framework import routers
from . import views

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'subscriptions', views.SubscriptionViewSet)
router.register(r'bookmarks', views.BookmarkViewSet)

urlpatterns = router.urls + [
    path('email', views.email_list),
    path('email/bookmark', views.email_bookmark),
    path('email/detail', views.email_detail),
    path('email/detail/info', views.email_detail_info),
    path('user/email-senders', views.email_senders),
    path('user', views.user_info),
]
