"""
Signals for initializing RAG components
"""
from django.conf import settings
import json
import logging
import os

logger = logging.getLogger(__name__)

# Global instances
rag_handler = None
model_handler = None
config = None


def init_rag_components():
    """Initialize RAG and Model handlers"""
    global rag_handler, model_handler, config
    
    # Load config
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("Loaded configuration")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        config = {
            "rag_options": {
                "delete_file_after_ingestion": False,
                "clear_database_on_start": False,
                "similarity_threshold": 0.3,
                "results_to_return": 2
            },
            "llm_options": {
                "system_prompt": "You are an assistant for question-answering tasks.",
                "temperature": 0.8,
                "tokens_to_generate": 256
            }
        }
    
    # Initialize handlers
    from .rag_handler import RAGHandler
    from .model_handler import ModelHandler
    
    try:
        rag_handler = RAGHandler(settings.DATABASE_FOLDER, config)
        logger.info("Initialized RAG handler")
    except Exception as e:
        logger.error(f"Error initializing RAG handler: {e}")
    
    try:
        model_handler = ModelHandler(settings.MODEL_NAME, settings.OLLAMA_ADDRESS, config)
        logger.info("Initialized Model handler")
    except Exception as e:
        logger.error(f"Error initializing Model handler: {e}")


# Initialize on import
init_rag_components()
