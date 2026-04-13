import uuid
from django.db import models

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    cpu = models.CharField(max_length=255, blank=True, null=True)
    ram = models.CharField(max_length=255, blank=True, null=True)
    disk = models.CharField(max_length=255, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='offline')
    last_seen = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.alias if self.alias else self.name
