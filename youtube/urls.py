from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('startFetching', views.startFetching, name='startFetching'),
    path('search', views.searchres, name='startFetching'),
]