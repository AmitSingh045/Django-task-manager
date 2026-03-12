from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.task_list, name='task_list'),
    path('add/', views.add_task, name='add_task'),
    path('edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    
    # Additional features
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/toggle/', views.toggle_task_status, name='toggle_task'),
    path('task/<int:task_id>/duplicate/', views.duplicate_task, name='duplicate_task'),
    
    # Bulk actions
    path('tasks/bulk-action/', views.bulk_task_action, name='bulk_task_action'),
    
    # Category views
    path('category/<int:category_id>/', views.category_tasks, name='category_tasks'),
    
    # Export
    path('export/', views.export_tasks, name='export_tasks'),
]