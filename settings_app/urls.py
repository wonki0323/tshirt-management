from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_settings, name='api_settings'),
]

