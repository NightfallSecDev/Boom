from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from clients.views import register_client, heartbeat
from tasks.views import get_task, submit_result
from files.views import download_script, upload_client_file, vault_page
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('core.urls')),
    path('vault/', vault_page, name='vault_page'),
    path('api/register/', register_client),
    path('api/heartbeat/', heartbeat),
    path('api/get-task/', get_task),
    path('api/submit-result/', submit_result),
    path('api/script/<str:script_id>/download/', download_script),
    path('api/upload-file/', upload_client_file),
]
