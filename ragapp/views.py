"""
Views for RAG application
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging

from . import signals

logger = logging.getLogger(__name__)


def index(request):
    """Main page with chat interface"""
    doc_count = 0
    if signals.rag_handler:
        doc_count = signals.rag_handler.get_document_count()
    
    context = {
        'document_count': doc_count,
        'model_name': settings.MODEL_NAME,
    }
    return render(request, 'ragapp/index.html', context)


@csrf_exempt
def upload_document(request):
    """Handle document upload"""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            uploaded_file = request.FILES['document']
            
            # Save file to ingestion folder
            file_path = os.path.join(settings.INGESTION_FOLDER, uploaded_file.name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            logger.info(f"File uploaded: {file_path}")
            
            # Check if RAG handler is available
            if not signals.rag_handler:
                return JsonResponse({
                    'success': False,
                    'message': 'RAG handler not initialized. Please check the logs.'
                })
            
            # Process document
            docs = signals.rag_handler.load_document(file_path)
            if docs:
                result = signals.rag_handler.add_document_to_chroma(docs, file_path)
                
                # Delete file after ingestion if configured
                if signals.config.get("rag_options", {}).get("delete_file_after_ingestion", False):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted after ingestion: {file_path}")
                
                if result.get('success'):
                    # Generate appropriate message based on duplicates
                    chunks_added = result.get('chunks_added', 0)
                    duplicates = result.get('duplicates_skipped', 0)
                    
                    if chunks_added == 0 and duplicates > 0:
                        message = f'Document "{uploaded_file.name}" was already in the database. All {duplicates} chunks were duplicates.'
                        message_type = 'warning'
                    elif duplicates > 0:
                        message = f'Document "{uploaded_file.name}" processed. Added {chunks_added} new chunks, skipped {duplicates} duplicates.'
                        message_type = 'info'
                    else:
                        message = f'Document "{uploaded_file.name}" uploaded and processed successfully. Added {chunks_added} chunks.'
                        message_type = 'success'
                    
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'message_type': message_type,
                        'document_count': signals.rag_handler.get_document_count(),
                        'db_stats': signals.rag_handler.get_database_stats(),
                        'chunks_added': chunks_added,
                        'duplicates_skipped': duplicates
                    })
                else:
                    error_msg = result.get('error', 'Unknown error')
                    return JsonResponse({
                        'success': False,
                        'message': f'Error processing document: {error_msg}'
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Failed to process document. Check file format or encoding.'
            })
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'No file provided'})


@csrf_exempt
def query(request):
    """Handle query requests"""
    if request.method == 'POST':
        try:
            user_query = request.POST.get('query', '')
            
            if not user_query:
                return JsonResponse({
                    'success': False,
                    'message': 'No query provided'
                })
            
            if not signals.model_handler:
                return JsonResponse({
                    'success': False,
                    'message': 'Model not initialized. Check Ollama connection.'
                })
            
            # Check if we have documents in the database
            use_rag = False
            related_docs = None
            
            if signals.rag_handler and signals.rag_handler.get_document_count() > 0:
                try:
                    related_docs = signals.rag_handler.get_docs_by_similarity(user_query)
                    if related_docs:
                        use_rag = True
                except Exception as e:
                    logger.error(f"Error getting similar docs: {e}")
            
            # Get response from model
            response = signals.model_handler.get_response(user_query, related_docs, use_rag)
            
            return JsonResponse({
                'success': True,
                'response': response,
                'used_rag': use_rag,
                'document_count': signals.rag_handler.get_document_count() if signals.rag_handler else 0
            })
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def status(request):
    """Get system status"""
    status_info = {
        'model_loaded': signals.model_handler is not None and signals.model_handler.model is not None,
        'rag_initialized': signals.rag_handler is not None,
        'document_count': 0,
        'model_name': settings.MODEL_NAME,
        'ollama_address': settings.OLLAMA_ADDRESS,
    }
    
    if signals.rag_handler:
        status_info['document_count'] = signals.rag_handler.get_document_count()
        # Add database statistics
        db_stats = signals.rag_handler.get_database_stats()
        status_info.update(db_stats)
    
    return JsonResponse(status_info)


@csrf_exempt
def clear_database(request):
    """Clear all documents from the database"""
    if request.method == 'POST':
        try:
            if not signals.rag_handler:
                return JsonResponse({
                    'success': False,
                    'message': 'RAG handler not initialized.'
                })
            
            success = signals.rag_handler.clear_database()
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Database cleared successfully.',
                    'document_count': 0,
                    'db_stats': {
                        'total_chunks': 0,
                        'unique_sources': 0,
                        'languages': {},
                        'file_types': {},
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to clear database. Check logs.'
                })
            
        except Exception as e:
            logger.error(f"Error clearing database: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
