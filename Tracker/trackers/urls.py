from . import views
from django.urls import path

urlpatterns = [
    path('about', views.about),
    path('Skeb', views.Skeb),
    path('', views.board,  name="board"),
    path('add_column/', views.add_column, name='add_column'),
    path('add_task/<int:column_id>/', views.add_task, name='add_task'),


]