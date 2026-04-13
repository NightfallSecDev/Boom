import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from clients.models import Client
from django.utils import timezone

@api_view(['POST'])
def register_client(request):
    name = request.data.get('name', 'Unknown')
    ip_address = request.META.get('REMOTE_ADDR')
    token = str(uuid.uuid4())
    
    client = Client.objects.create(
        name=name,
        ip_address=ip_address,
        token=token,
        status='online',
        os_version=request.data.get('os_version', ''),
        cpu=request.data.get('cpu', ''),
        ram=request.data.get('ram', ''),
        disk=request.data.get('disk', ''),
        mac_address=request.data.get('mac_address', ''),
        tags=request.data.get('tags', '')
    )
    return Response({'id': client.id, 'token': token})

@api_view(['POST'])
def heartbeat(request):
    token = request.data.get('token')
    try:
        client = Client.objects.get(token=token)
        client.last_seen = timezone.now()
        client.status = 'online'
        client.os_version = request.data.get('os_version', client.os_version)
        client.cpu = request.data.get('cpu', client.cpu)
        client.ram = request.data.get('ram', client.ram)
        client.disk = request.data.get('disk', client.disk)
        client.save()
        return Response({'status': 'ok'})
    except Client.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=401)
