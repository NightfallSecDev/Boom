import uuid
from django.db import models
from tasks.models import Task

class ScriptFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='scripts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ClientFileTransfer(models.Model):
    DIRECTION_CHOICES = (
        ('upload', 'To Client'),
        ('download', 'From Client'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='file_transfers')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    file = models.FileField(upload_to='transfers/')
    created_at = models.DateTimeField(auto_now_add=True)
