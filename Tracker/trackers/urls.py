from django.urls import path
from . import views

urlpatterns = [
    path('about', views.about),
    path('Skeb', views.Skeb),
    path('', views.board, name='board'),

    path('add_column/', views.add_column, name='add_column'),
    path('add_task/<int:column_id>/', views.add_task, name='add_task'),

    #для drag & drop
    path('api/tasks/move/', views.move_task, name='task_move'),
]
