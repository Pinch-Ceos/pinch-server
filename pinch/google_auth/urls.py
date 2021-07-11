from django.urls import path
from . import views

app_name = 'google_auth'

urlpatterns = [
    path('login', views.google_login),
    path('callback', views.google_callback),
]
