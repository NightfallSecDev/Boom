import uuid
from django.db import models
from clients.models import Client

class JobBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class TaskTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    command = models.TextField()
    
    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(JobBatch, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    command = models.TextField()
    target_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.command[:20]} - {self.status}"
