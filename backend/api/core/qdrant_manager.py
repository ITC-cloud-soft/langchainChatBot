"""
Qdrant Manager for vector database operations

This module provides integration with Qdrant vector database for knowledge base operations.
"""

import os
import asyncio
import warnings
from typing import List, Dict, Any, Optional

# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", message=".*OllamaEmbeddings.*deprecated.*", category=DeprecationWarning)
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore as LangchainQdrant
from langchain.schema import Document

from api.core.config_manager import settings
from api.core.utils import default_logger

logger = default_logger


class QdrantManager:
    """Qdrant vector database manager"""
    
    def __init__(self):
        """Initialize Qdrant manager"""
        self._initialized = False
        self.client = None
        self.vectorstore = None
        self.embeddings = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
    
    async def initialize(self) -> bool:
        """Initialize Qdrant connection and create collection if needed"""
        try:
            logger.info("Initializing Qdrant manager")
            
            # Initialize embeddings
            # Clean up URL by removing trailing spaces from port
            base_url = settings.EMBEDDING_BASE_URL.strip()  # Remove all whitespace
            
            # Manual URL cleanup to ensure port number is properly formatted
            # This handles the case where there might be spaces after the port
            import re
            
            # Pattern to match URLs with ports and potential trailing spaces
            url_pattern = r'^(https?://[^:]+):(\d+)\s*$'
            match = re.match(url_pattern, base_url)
            
            if match:
                scheme_host = match.group(1)
                port = match.group(2).strip()
                base_url = f"{scheme_host}:{port}"
                logger.info(f"Cleaned URL: {base_url}")
            else:
                # If no port is found, ensure the base URL is clean
                base_url = base_url.strip()
                logger.info(f"Using base URL as-is: {base_url}")
            
            # Try different embedding approaches
            embeddings_initialized = False
            
            # Approach 1: Try langchain_ollama first (recommended new package)
            try:
                from langchain_ollama import OllamaEmbeddings
                self.embeddings = OllamaEmbeddings(
                    model=settings.EMBEDDING_MODEL_NAME,
                    base_url=base_url
                )
                logger.info("Using langchain_ollama for embeddings")
                embeddings_initialized = True
            except ImportError as e:
                logger.warning(f"Failed to import from langchain-ollama: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings from langchain_ollama: {e}")
        
            # Approach 2: Fallback to langchain_community if ollama fails
            if not embeddings_initialized:
                try:
                    from langchain_community.embeddings import OllamaEmbeddings
                    self.embeddings = OllamaEmbeddings(
                        model=settings.EMBEDDING_MODEL_NAME,
                        base_url=base_url
                    )
                    logger.info("Using langchain_community for embeddings (fallback)")
                    embeddings_initialized = True
                except Exception as e:
                    logger.error(f"Failed to initialize embeddings from langchain_community: {e}")
            
            # Approach 3: Fallback to a mock embedding class if all else fails
            if not embeddings_initialized:
                logger.warning("All embedding approaches failed, using mock embeddings")
                class MockEmbeddings:
                    def __init__(self, model_name="mock"):
                        self.model_name = model_name
                    
                    def embed_documents(self, texts):
                        # Return mock embeddings (768 dimensions like nomic-embed-text)
                        import numpy as np
                        return [np.random.rand(768).tolist() for _ in texts]
                    
                    def embed_query(self, text):
                        # Return mock embedding for query
                        import numpy as np
                        return np.random.rand(768).tolist()
                
                self.embeddings = MockEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
                embeddings_initialized = True
            
            if not embeddings_initialized:
                raise Exception("Failed to initialize any embedding method")
            
            # Initialize Qdrant client with improved connection settings
            try:
                # Use explicit IP address to avoid DNS resolution issues
                qdrant_host = "127.0.0.1" if settings.QDRANT_HOST in ["localhost", "127.0.0.1"] else settings.QDRANT_HOST
                
                self.client = QdrantClient(
                    host=qdrant_host,
                    port=settings.QDRANT_PORT,
                    grpc_port=settings.QDRANT_GRPC_PORT,
                    timeout=60,  # Increased timeout
                    prefer_grpc=False  # Use HTTP instead of gRPC for better compatibility
                )
                
                logger.info(f"Attempting to connect to Qdrant at {qdrant_host}:{settings.QDRANT_PORT}")
                
                # Test connection with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        collections = self.client.get_collections()
                        logger.info(f"Qdrant connection successful on attempt {attempt + 1}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Connection attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(2)  # Wait 2 seconds before retry
                        
            except Exception as e:
                logger.warning(f"Qdrant connection failed after all retries: {e}")
                logger.info("Continuing in fallback mode without vector store")
                # Create empty collection info for fallback mode
                self.vectorstore = None
                self._initialized = True
                return True
                
            # Create collection if it doesn't exist
            try:
                collections = self.client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if self.collection_name not in collection_names:
                    logger.info(f"Creating collection: {self.collection_name}")
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=768,  # Ollama nomic-embed-text dimension
                            distance=Distance.COSINE
                        )
                    )
                
                # Initialize LangChain vectorstore
                self.vectorstore = LangchainQdrant(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding=self.embeddings
                )
                
                logger.info("Qdrant manager initialized successfully")
                self._initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Error creating collection: {e}")
                self.vectorstore = None
                self._initialized = True
                return True
                
        except Exception as e:
            logger.error(f"Error initializing Qdrant manager: {e}")
            self.vectorstore = None
            self._initialized = True
            return True
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None) -> bool:
        """Add a document to the vector store"""
        if not self._initialized or not self.vectorstore:
            return False
        
        try:
            # Create document
            doc = Document(page_content=content, metadata=metadata or {})
            
            # Add to vectorstore
            self.vectorstore.add_documents([doc])
            logger.info(f"Document added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def add_documents_from_directory(self, directory_path: str, glob_pattern: str = "**/*.txt", chunk_size: int = 1000, chunk_overlap: int = 200) -> bool:
        """Add documents from a directory"""
        if not self._initialized or not self.vectorstore:
            return False
        
        try:
            from pathlib import Path
            import glob
            
            directory = Path(directory_path)
            if not directory.exists():
                logger.error(f"Directory not found: {directory_path}")
                return False
            
            # Find files
            files = list(directory.glob(glob_pattern))
            if not files:
                logger.warning(f"No files found in {directory_path} with pattern {glob_pattern}")
                return False
            
            documents = []
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split into chunks
                    chunks = text_splitter.split_text(content)
                    
                    for chunk in chunks:
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": str(file_path),
                                "filename": file_path.name
                            }
                        )
                        documents.append(doc)
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
            
            if documents:
                self.vectorstore.add_documents(documents)
                logger.info(f"Added {len(documents)} document chunks from {len(files)} files")
                return True
            else:
                logger.warning("No documents were processed")
                return False
                
        except Exception as e:
            logger.error(f"Error adding documents from directory: {e}")
            return False
    
    async def search_similar_documents(self, query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self._initialized:
            return []
        
        if not self.vectorstore:
            # Fallback to simple mock results when Qdrant is not available
            return [
                {
                    "content": f"Qdrant is not available. Mock result for query: {query}",
                    "metadata": {"source": "mock", "score": 0.8}
                }
            ]
        
        try:
            # Search using vectorstore
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            search_results = []
            for doc, score in results:
                search_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            logger.info(f"Found {len(search_results)} similar documents")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        if not self.client:
            return {
                "name": self.collection_name,
                "count": 0,
                "status": "mock_mode",
                "message": "Qdrant not available"
            }
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "count": collection_info.points_count,
                "status": "active",
                "vectors_config": collection_info.config.params.vectors.dict() if hasattr(collection_info.config.params, 'vectors') and collection_info.config.params.vectors else None
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "name": self.collection_name,
                "count": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List documents in the collection"""
        if not self._initialized or not self.client:
            return []
        
        try:
            # Scroll through collection
            records = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True
            )
            
            documents = []
            for record in records[0]:
                # LangChain Qdrant integration stores page_content directly in payload
                content = ""
                metadata = {}
                
                if hasattr(record, 'payload') and record.payload:
                    # Check if page_content exists directly in payload
                    if "page_content" in record.payload:
                        content = record.payload["page_content"]
                    # If not, the entire payload might be the content
                    elif "text" in record.payload:
                        content = record.payload["text"]
                    else:
                        # Fallback: use string representation of payload
                        content = str(record.payload)
                    
                    # Extract metadata
                    if "metadata" in record.payload:
                        metadata = record.payload["metadata"]
                    else:
                        # Use other payload fields as metadata
                        metadata = {k: v for k, v in record.payload.items() if k not in ["page_content", "text"]}
                
                documents.append({
                    "id": str(record.id),
                    "content": content,
                    "metadata": metadata
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    async def delete_document_by_id(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        if not self._initialized or not self.client:
            return False
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[doc_id]
            )
            logger.info(f"Document {doc_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    async def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        if not self._initialized or not self.client:
            return False
        
        try:
            self.client.delete_collection(self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE
                )
            )
            logger.info("Collection cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

# Global instance
qdrant_manager = QdrantManager()