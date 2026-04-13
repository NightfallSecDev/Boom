from django.contrib import admin
from .models import Log

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'executed_at')
