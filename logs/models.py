import uuid
from django.db import models
from tasks.models import Task

class Log(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='log')
    output = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for Task {self.task.id}"
