from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'alias', 'ip_address', 'os_version', 'status', 'last_seen')
    search_fields = ('name', 'alias', 'ip_address', 'mac_address')
    list_filter = ('status', 'os_version')
