"""
RAG App Configuration
"""
from django.apps import AppConfig


class RagappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ragapp'
    
    def ready(self):
        """Initialize RAG components when Django starts"""
        from . import signals
