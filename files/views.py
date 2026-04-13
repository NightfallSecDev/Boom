import os
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from files.models import ScriptFile, ClientFileTransfer
from tasks.models import Task
from clients.models import Client

@login_required
def vault_page(request):
    if request.method == 'POST' and request.FILES.get('script_file'):
        file = request.FILES['script_file']
        ScriptFile.objects.create(name=request.POST.get('name', file.name), file=file)
        return redirect('vault_page')
        
    scripts = ScriptFile.objects.all().order_by('-uploaded_at')
    transfers = ClientFileTransfer.objects.all().order_by('-created_at')
    return render(request, 'core/vault.html', {'scripts': scripts, 'transfers': transfers})

@api_view(['GET'])
def download_script(request, script_id):
    try:
        script = ScriptFile.objects.get(id=script_id)
        if os.path.exists(script.file.path):
            with open(script.file.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(script.file.name)}"'
                return response
    except ScriptFile.DoesNotExist:
        pass
    return JsonResponse({'error': 'Not found'}, status=404)

@api_view(['POST'])
def upload_client_file(request):
    token = request.data.get('token')
    task_id = request.data.get('task_id')
    uploaded_file = request.FILES.get('file')
    
    if not token or not task_id or not uploaded_file:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    try:
        client = Client.objects.get(token=token)
        task = Task.objects.get(id=task_id, target_client=client)
        ClientFileTransfer.objects.create(
            task=task,
            direction='download',
            file=uploaded_file
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
