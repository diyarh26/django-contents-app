from django.urls import path
from . import views

urlpatterns = [
path('', views.home, name='home'),
path('feedback/', views.moviefeedback, name='feedback'),
path('query/', views.query, name='query'),
path('addactor/', views.addactor, name='addactor'),
]