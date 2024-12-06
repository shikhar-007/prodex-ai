from django.urls import path
from . import views


urlpatterns = [
    path('ask-question/', views.ask_question, name='ask_question'),
    ]
