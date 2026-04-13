from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/terminal/(?P<task_id>[\w-]+)/$', consumers.TerminalConsumer.as_asgi()),
    re_path(r'ws/agent/(?P<token>[\w-]+)/$', consumers.AgentConsumer.as_asgi()),
]
