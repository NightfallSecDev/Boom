from django.contrib import admin
from .models import JobBatch, TaskTemplate, Task

@admin.register(JobBatch)
class JobBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch', 'target_client', 'status', 'created_at')
    list_filter = ('status',)
