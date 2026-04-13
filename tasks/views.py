from rest_framework.decorators import api_view
from rest_framework.response import Response
from tasks.models import Task
from clients.models import Client
from logs.models import Log

@api_view(['POST'])
def get_task(request):
    token = request.data.get('token')
    try:
        client = Client.objects.get(token=token)
    except Client.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=401)
        
    task = Task.objects.filter(target_client=client, status='pending').order_by('created_at').first()
    if task:
        task.status = 'assigned'
        task.save()
        return Response({
            'task_id': task.id,
            'command': task.command
        })
    return Response({'message': 'No pending tasks'})

@api_view(['POST'])
def submit_result(request):
    token = request.data.get('token')
    task_id = request.data.get('task_id')
    output = request.data.get('output', '')
    error = request.data.get('error', '')
    
    try:
        client = Client.objects.get(token=token)
    except Client.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=401)
        
    try:
        task = Task.objects.get(id=task_id, target_client=client)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)
        
    task.status = 'completed'
    task.save()
    
    Log.objects.create(
        task=task,
        output=output,
        error=error
    )
    
    return Response({'status': 'ok'})
