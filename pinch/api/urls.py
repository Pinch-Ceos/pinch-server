from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('email_senders', views.email_senders),
]
