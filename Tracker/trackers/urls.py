from django.urls import path
from . import views

urlpatterns = [
    path('about', views.about),
    path('Skeb', views.Skeb),
    path('', views.board, name='board'),


    path('add_column/', views.add_column, name='add_column'),
    path('add_task/<int:column_id>/', views.add_task, name='add_task'),

    #для drag and drop
    path('api/tasks/move/', views.move_task, name='task_move'),

    #Редагування
    path('edit_column/<int:column_id>/', views.edit_column, name='edit_column'),
    path('edit_task/<int:task_id>/', views.edit_task, name='edit_task'),


    path('delete_column/<int:column_id>/', views.delete_column, name='delete_column'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
]
