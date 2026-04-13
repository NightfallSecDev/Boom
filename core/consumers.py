import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'terminal_{self.task_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # We receive inputs from the web UI to route to the agent
        try:
            text_data_json = json.loads(text_data)
            stdin_cmd = text_data_json.get('command')
            
            if stdin_cmd:
                await self.channel_layer.group_send(
                    f'agent_stream_{self.task_id}',
                    {
                        'type': 'agent_input',
                        'command': stdin_cmd
                    }
                )
        except Exception as e:
            await self.send(text_data=json.dumps({'output': f'\r\n[STREAM ERROR] {str(e)}\r\n'}))

    async def terminal_output(self, event):
        # Used to broadcast agent stdout back to the Web UI
        try:
            message = event['message']
            await self.send(text_data=json.dumps({
                'output': message
            }))
        except Exception:
            pass


class AgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.token = self.scope['url_route']['kwargs']['token']
        # Instead of binding to a specific task initially, bind to the agent's general queue
        self.group_name = f'agent_{self.token}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # The agent sends live stdout updates formatted generally like {"task_id": "123", "output": "..."}
        try:
            data = json.loads(text_data)
            task_id = data.get('task_id')
            output = data.get('output')
            
            if task_id and output:
                # Forward to the terminal viewer
                await self.channel_layer.group_send(
                    f'terminal_{task_id}',
                    {
                        'type': 'terminal_output',
                        'message': output
                    }
                )
        except Exception:
            pass

    async def execute_task(self, event):
        # Master server pushes a custom shell interactive socket setup request
        try:
            task_id = event['task_id']
            command = event['command']
            await self.send(text_data=json.dumps({
                'action': 'execute',
                'task_id': task_id,
                'command': command
            }))
        except Exception:
            pass
        
    async def agent_input(self, event):
        # Piped standard inputs routed into the agent process
        try:
            command = event['command']
            await self.send(text_data=json.dumps({
                'action': 'input',
                'command': command
            }))
        except Exception:
            pass
