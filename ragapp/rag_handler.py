"""
RAG Handler for document loading, splitting, and similarity search with semantic chunking
"""
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, csv_loader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from datetime import datetime
import hashlib
import re
import logging

# Optional: Semantic chunking (requires langchain_experimental)
try:
    from langchain_experimental.text_splitter import SemanticChunker
    SEMANTIC_CHUNKER_AVAILABLE = True
except ImportError:
    SEMANTIC_CHUNKER_AVAILABLE = False
    logging.warning("langchain_experimental not available, semantic chunking will fall back to recursive splitting")

# Optional: Language detection
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning("langdetect not available, language detection will be skipped")

logger = logging.getLogger(__name__)


class RAGHandler:
    def __init__(self, database_folder, config):
        self.database_folder = database_folder
        self.config = config
        
        # Initialize embedding function for semantic chunking
        self.embedding_function = FastEmbedEmbeddings()
        
        # Initialize different splitters for different document types
        self._initialize_splitters()
        
        self.vector_store = self.initialize_chroma()

    def _initialize_splitters(self):
        """Initialize different text splitters for semantic chunking"""
        
        # Semantic chunker - uses embeddings to find natural breakpoints
        # Best for narrative text, documentation, articles
        if SEMANTIC_CHUNKER_AVAILABLE:
            self.semantic_splitter = SemanticChunker(
                self.embedding_function,
                breakpoint_threshold_type="percentile",  # Uses percentile of differences
                breakpoint_threshold_amount=80  # Split at top 20% of semantic differences
            )
            logger.info("Semantic chunker initialized successfully")
        else:
            # Fallback to recursive splitter for text files
            self.semantic_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n\n", "\n\n", "\n", ". ", ", ", " ", ""]
            )
            logger.info("Using recursive splitter as fallback for semantic chunking")
        
        # Recursive splitter with smart separators for structured documents
        # Good for PDFs, technical docs with sections
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=[
                "\n\n\n",  # Document sections
                "\n\n",    # Paragraphs
                "\n",      # Lines
                ". ",      # Sentences
                ", ",      # Clauses
                " ",       # Words
                ""         # Characters
            ]
        )
        
        # Smaller chunks for CSV data (each row should be meaningful)
        self.csv_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n", ", ", " ", ""]
        )

    def initialize_chroma(self):
        return Chroma(
            collection_name="information",
            persist_directory=self.database_folder,
            embedding_function=self.embedding_function,
        )

    def load_document(self, file_path):
        """Load the document based on the file extension"""
        loader = None
        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
            elif file_path.endswith(".csv"):
                loader = csv_loader.CSVLoader(file_path)
            elif file_path.endswith(".txt"):
                # Try UTF-8 first, then fall back to other encodings
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return None
            return loader.load()
        except UnicodeDecodeError:
            # Try with different encoding for text files
            try:
                logger.info(f"UTF-8 failed, trying latin-1 encoding for {file_path}")
                loader = TextLoader(file_path, encoding='latin-1')
                return loader.load()
            except Exception as e:
                logger.error(f"Error loading document with fallback encoding: {e}")
                return None
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None

    def add_document_to_chroma(self, document, file_path=None):
        """Add document to the vector store using appropriate chunking strategy"""
        if document is None:
            logger.error("Failed to load document.")
            return False
        try:
            # Select appropriate splitter based on document type
            splitter = self._get_splitter_for_document(file_path)
            
            chunks = splitter.split_documents(document)
            
            # Enrich metadata for each chunk
            enriched_chunks = self._enrich_metadata(chunks, file_path)
            
            # Deduplicate chunks based on content hash
            unique_chunks, duplicate_count = self._deduplicate_chunks(enriched_chunks)
            
            # Log chunking info
            logger.info(f"Split document into {len(chunks)} semantic chunks")
            if duplicate_count > 0:
                logger.info(f"Removed {duplicate_count} duplicate chunks")
            logger.info(f"Adding {len(unique_chunks)} unique chunks to database")
            
            if unique_chunks:
                avg_chunk_size = sum(len(chunk.page_content) for chunk in unique_chunks) / len(unique_chunks)
                logger.info(f"Average chunk size: {avg_chunk_size:.0f} characters")
            
            if unique_chunks:
                self.vector_store.add_documents(unique_chunks)
                logger.info("Added document to the database.")
            
            # Return success with metadata about the operation
            return {
                'success': True,
                'chunks_added': len(unique_chunks),
                'duplicates_skipped': duplicate_count,
                'total_chunks': len(chunks)
            }
        except Exception as e:
            logger.error(f"Error adding document to database: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _enrich_metadata(self, chunks, file_path):
        """Enrich each chunk with comprehensive metadata"""
        enriched_chunks = []
        timestamp = datetime.utcnow().isoformat()
        file_type = self._get_file_type(file_path) if file_path else "unknown"
        source = file_path.split('\\')[-1] if file_path else "unknown"
        
        for idx, chunk in enumerate(chunks):
            content = chunk.page_content
            
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
            
            # Extract text features
            word_count = len(content.split())
            char_count = len(content)
            has_numbers = bool(re.search(r'\d', content))
            has_urls = bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content))
            
            # Detect language
            language = self._detect_language(content)
            
            # Create enriched metadata
            enriched_metadata = {
                **chunk.metadata,  # Preserve original metadata
                'source': source,
                'chunk_id': f"{source}_{idx}_{content_hash[:8]}",
                'file_type': file_type,
                'timestamp': timestamp,
                'word_count': word_count,
                'char_count': char_count,
                'language': language,
                'content_hash': content_hash,
                'has_numbers': has_numbers,
                'has_urls': has_urls,
                'chunk_index': idx,
            }
            
            chunk.metadata = enriched_metadata
            enriched_chunks.append(chunk)
        
        return enriched_chunks

    def _deduplicate_chunks(self, chunks):
        """Remove duplicate chunks based on content hash"""
        seen_hashes = set()
        unique_chunks = []
        duplicate_count = 0
        
        # Check existing hashes in the database
        try:
            existing_collection = self.vector_store._collection
            existing_metadata = existing_collection.get(include=['metadatas'])
            
            if existing_metadata and existing_metadata.get('metadatas'):
                for metadata in existing_metadata['metadatas']:
                    if metadata and 'content_hash' in metadata:
                        seen_hashes.add(metadata['content_hash'])
                
                logger.info(f"Found {len(seen_hashes)} existing hashes in database")
        except Exception as e:
            logger.warning(f"Could not check existing hashes: {e}")
        
        # Filter new chunks
        for chunk in chunks:
            content_hash = chunk.metadata.get('content_hash')
            
            if content_hash and content_hash in seen_hashes:
                duplicate_count += 1
                logger.debug(f"Skipping duplicate chunk: {chunk.metadata.get('chunk_id')}")
            else:
                if content_hash:
                    seen_hashes.add(content_hash)
                unique_chunks.append(chunk)
        
        return unique_chunks, duplicate_count

    def _detect_language(self, text):
        """Detect the language of the text"""
        if not LANGDETECT_AVAILABLE:
            return "unknown"
        
        try:
            # Only try to detect if text is long enough
            if len(text) < 20:
                return "unknown"
            return detect(text)
        except LangDetectException:
            return "unknown"
        except Exception as e:
            logger.debug(f"Language detection error: {e}")
            return "unknown"

    def _get_file_type(self, file_path):
        """Extract file type from file path"""
        if not file_path:
            return "unknown"
        
        file_path_lower = file_path.lower()
        if file_path_lower.endswith('.pdf'):
            return "pdf"
        elif file_path_lower.endswith('.docx'):
            return "docx"
        elif file_path_lower.endswith('.txt'):
            return "txt"
        elif file_path_lower.endswith('.csv'):
            return "csv"
        else:
            return "unknown"

    def _get_splitter_for_document(self, file_path):
        """Select the appropriate text splitter based on document type"""
        if not file_path:
            return self.recursive_splitter
        
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.txt') or file_path_lower.endswith('.docx'):
            # Use semantic chunking for narrative text documents
            strategy = "semantic" if SEMANTIC_CHUNKER_AVAILABLE else "recursive (fallback)"
            logger.info(f"Using {strategy} chunking for text/DOCX document")
            return self.semantic_splitter
        elif file_path_lower.endswith('.csv'):
            # Use smaller chunks for CSV data
            logger.info("Using CSV-optimized chunking")
            return self.csv_splitter
        elif file_path_lower.endswith('.pdf'):
            # Use recursive splitter with smart separators for PDFs
            logger.info("Using recursive chunking with smart separators for PDF")
            return self.recursive_splitter
        else:
            # Default fallback
            logger.info("Using default recursive chunking")
            return self.recursive_splitter

    def get_docs_by_similarity(self, query):
        """Get similar documents from the vector store with enriched metadata"""
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=self.config["rag_options"]["results_to_return"],
            score_threshold=self.config["rag_options"]["similarity_threshold"],
        )
        
        # Log metadata for retrieved chunks
        for doc, score in results:
            metadata = doc.metadata
            logger.debug(f"Retrieved chunk: {metadata.get('chunk_id', 'unknown')} "
                        f"(score: {score:.3f}, lang: {metadata.get('language', 'unknown')}, "
                        f"words: {metadata.get('word_count', 0)})")
        
        return results
    
    def get_document_count(self):
        """Get the number of unique source documents in the database"""
        try:
            collection = self.vector_store._collection
            result = collection.get(include=['metadatas'])
            
            if not result or not result.get('metadatas'):
                return 0
            
            # Count unique source documents
            sources = set()
            for metadata in result['metadatas']:
                if metadata and 'source' in metadata:
                    sources.add(metadata['source'])
            
            return len(sources)
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def get_database_stats(self):
        """Get statistics about the database including metadata insights"""
        try:
            collection = self.vector_store._collection
            result = collection.get(include=['metadatas'])
            
            if not result or not result.get('metadatas'):
                return {
                    'total_chunks': 0,
                    'unique_sources': 0,
                    'languages': {},
                    'file_types': {},
                }
            
            metadatas = result['metadatas']
            sources = set()
            languages = {}
            file_types = {}
            
            for metadata in metadatas:
                if not metadata:
                    continue
                
                # Collect unique sources
                if 'source' in metadata:
                    sources.add(metadata['source'])
                
                # Count languages
                lang = metadata.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
                
                # Count file types
                ftype = metadata.get('file_type', 'unknown')
                file_types[ftype] = file_types.get(ftype, 0) + 1
            
            return {
                'total_chunks': len(metadatas),
                'unique_sources': len(sources),
                'languages': languages,
                'file_types': file_types,
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                'total_chunks': 0,
                'unique_sources': 0,
                'languages': {},
                'file_types': {},
            }
    
    def clear_database(self):
        """Clear all documents from the database"""
        try:
            self.vector_store.reset_collection()
            logger.info("Database cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
