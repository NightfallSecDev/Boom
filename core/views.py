from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from files.models import ScriptFile
from clients.models import Client
from tasks.models import Task, JobBatch
from logs.models import Log

# =======================
# Web Dashboard Views
# =======================

@login_required
def dashboard(request):
    total_clients = Client.objects.count()
    online_clients = Client.objects.filter(status='online').count()
    offline_clients = total_clients - online_clients
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    context = {
        'total_clients': total_clients,
        'online_clients': online_clients,
        'offline_clients': offline_clients,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def clients_page(request):
    clients = Client.objects.all().order_by('-last_seen')
    return render(request, 'core/clients.html', {'clients': clients})

@login_required
def tasks_page(request):
    if request.method == 'POST':
        command = request.POST.get('command')
        script_id = request.POST.get('script_id')
        client_ids = request.POST.getlist('client_ids')
        
        if script_id:
            command = f"loom_run_script {script_id}"
            
        if command and client_ids:
            try:
                batch = JobBatch.objects.create(name=f"Batch {timezone.now().strftime('%Y%m%d%H%M%S')}")
                channel_layer = get_channel_layer()
                for cid in client_ids:
                    try:
                        client = Client.objects.get(id=cid)
                        task = Task.objects.create(batch=batch, command=command, target_client=client)
                        
                        # Dispatch real-time web-socket signal
                        async_to_sync(channel_layer.group_send)(
                            f"agent_{client.token}",
                            {
                                "type": "execute_task",
                                "task_id": str(task.id),
                                "command": command
                            }
                        )
                    except Client.DoesNotExist:
                        pass
                    except Exception as e:
                        print(f"[ERROR] Task dispatch error: {e}")
            except Exception as e:
                print(f"[CRITICAL ERROR] Batch creation failed: {e}")
            return redirect('tasks_page')
            
    tasks = Task.objects.all().order_by('-created_at')[:20]
    clients = Client.objects.all()
    
    batches = JobBatch.objects.all().order_by('-created_at')[:10]
    batch_data = []
    for b in batches:
        total = b.tasks.count()
        completed = b.tasks.filter(status='completed').count()
        progress = (completed / total * 100) if total > 0 else 0
        batch_data.append({
            'batch': b,
            'total': total,
            'completed': completed,
            'progress': int(progress)
        })
        
    scripts = ScriptFile.objects.all()
        
    return render(request, 'core/tasks.html', {'tasks': tasks, 'clients': clients, 'batches': batch_data, 'scripts': scripts})

@login_required
def explorer_page(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        client_id = request.POST.get('client_id')
        
        if not client_id:
            return JsonResponse({'error': 'No client ID'})
            
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Client not found'})
            
        channel_layer = get_channel_layer()

        if action == 'list':
            target_path = request.POST.get('path', '.')
            if target_path.strip() == '': target_path = '.'
            try:
                command = f"loom_fs_list {target_path}"
                task = Task.objects.create(command=command, target_client=client)
                async_to_sync(channel_layer.group_send)(
                    f"agent_{client.token}",
                    {"type": "execute_task", "task_id": str(task.id), "command": command}
                )
                return JsonResponse({"task_id": str(task.id)})
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        elif action == 'download':
            target_path = request.POST.get('path', '')
            try:
                command = f"loom_fs_download {target_path}"
                task = Task.objects.create(command=command, target_client=client)
                async_to_sync(channel_layer.group_send)(
                    f"agent_{client.token}",
                    {"type": "execute_task", "task_id": str(task.id), "command": command}
                )
                return JsonResponse({"task_id": str(task.id)})
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        elif action == 'upload':
            uploaded_file = request.FILES.get('file')
            target_dir = request.POST.get('target_dir', '.')
            if uploaded_file:
                try:
                    import os
                    score_name = uploaded_file.name
                    script = ScriptFile.objects.create(name=score_name, file=uploaded_file)
                    dest_path = os.path.join(target_dir, score_name).replace('\\', '/')
                    command = f"loom_fs_upload {script.id} {dest_path}"
                    task = Task.objects.create(command=command, target_client=client)
                    async_to_sync(channel_layer.group_send)(
                        f"agent_{client.token}",
                        {"type": "execute_task", "task_id": str(task.id), "command": command}
                    )
                    return JsonResponse({"task_id": str(task.id)})
                except Exception as e:
                    return JsonResponse({"error": str(e)}, status=500)

    clients = Client.objects.all().order_by('-last_seen')
    return render(request, 'core/explorer.html', {'clients': clients})

@login_required
def logs_page(request):
    logs = Log.objects.all().order_by('-executed_at')
    return render(request, 'core/logs.html', {'logs': logs})

@login_required
def task_status_api(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        data = {
            'status': task.status,
            'output': '',
            'error': ''
        }
        if hasattr(task, 'log'):
            data['output'] = task.log.output
            data['error'] = task.log.error
        return JsonResponse(data)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required
@csrf_exempt
def terminate_client_api(request, client_id):
    if request.method == 'POST':
        try:
            client = get_object_or_404(Client, id=client_id)
            task = Task.objects.create(command="loom_kill_switch", target_client=client)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"agent_{client.token}",
                {
                    "type": "execute_task",
                    "task_id": str(task.id),
                    "command": "loom_kill_switch"
                }
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def purge_offline_clients_api(request):
    if request.method == 'POST':
        try:
            deleted_count, _ = Client.objects.filter(status='offline').delete()
            return JsonResponse({'status': 'ok', 'deleted_count': deleted_count})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)
