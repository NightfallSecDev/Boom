from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clients/', views.clients_page, name='clients_page'),
    path('tasks/', views.tasks_page, name='tasks_page'),
    path('explorer/', views.explorer_page, name='explorer_page'),
    path('logs/', views.logs_page, name='logs_page'),
    path('api/task/<str:task_id>/', views.task_status_api, name='task_status_api'),
    path('api/client/<uuid:client_id>/terminate/', views.terminate_client_api, name='terminate_client_api'),
    path('api/clients/purge/', views.purge_offline_clients_api, name='purge_offline_clients_api'),
]
