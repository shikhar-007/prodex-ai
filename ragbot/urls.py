from django.urls import path
from . import views
from .views import handle_user_query

urlpatterns = [
    path('query/', handle_user_query, name='query'),
    # path('ask-question/', views.ask_question, name='ask_question'),
    ]
