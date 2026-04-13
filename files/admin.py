from django.contrib import admin
from .models import ScriptFile, ClientFileTransfer

@admin.register(ScriptFile)
class ScriptFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at')

@admin.register(ClientFileTransfer)
class ClientFileTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'direction', 'created_at')
    list_filter = ('direction',)
