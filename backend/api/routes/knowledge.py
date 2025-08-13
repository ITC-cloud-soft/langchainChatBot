"""
Knowledge Management API routes for the Chatbot System

This module provides API endpoints for managing knowledge base.
"""

import os
import shutil
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from api.core.qdrant_manager import qdrant_manager
from api.core.config_manager import settings
from api.core.config_manager import config_manager
from api.core.utils import handle_exceptions, default_logger, format_success_response

# Create router
router = APIRouter()

# Pydantic models
class KnowledgeDocument(BaseModel):
    """Knowledge document model"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    doc_id: Optional[str] = None

class KnowledgeResponse(BaseModel):
    """Knowledge response model"""
    success: bool
    message: str
    doc_id: Optional[str] = None
    document_count: Optional[int] = None

class KnowledgeSearchRequest(BaseModel):
    """Knowledge search request model"""
    query: str
    k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None

class KnowledgeSearchResponse(BaseModel):
    """Knowledge search response model"""
    results: List[Dict[str, Any]]
    count: int

class CollectionInfo(BaseModel):
    """Collection info model"""
    name: str
    count: int
    metadata: Dict[str, Any]

class DocumentList(BaseModel):
    """Document list model"""
    documents: List[Dict[str, Any]]
    count: int

@router.post("/document", response_model=KnowledgeResponse)
async def add_document(document: KnowledgeDocument):
    """Add a single document to the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Add document
        success = await qdrant_manager.add_document(
            content=document.content,
            metadata=document.metadata,
            doc_id=document.doc_id
        )
        
        if success:
            # Get collection info to return document count
            collection_info = await qdrant_manager.get_collection_info()
            document_count = collection_info.get("count", 0)
            
            return KnowledgeResponse(
                success=True,
                message="Document added successfully",
                doc_id=document.doc_id,
                document_count=document_count
            )
        else:
            return KnowledgeResponse(
                success=False,
                message="Failed to add document"
            )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error adding document: {str(e)}"
        )

@router.post("/documents/upload", response_model=KnowledgeResponse)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """Upload a document file to the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Parse metadata if provided
        doc_metadata = {}
        if metadata:
            import json
            try:
                doc_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                doc_metadata = {"source": "uploaded_file"}
        else:
            doc_metadata = {"source": "uploaded_file", "filename": file.filename}
        
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8")
        
        # Add document
        success = await qdrant_manager.add_document(
            content=text_content,
            metadata=doc_metadata,
            doc_id=file.filename
        )
        
        if success:
            # Get collection info to return document count
            collection_info = await qdrant_manager.get_collection_info()
            document_count = collection_info.get("count", 0)
            
            return KnowledgeResponse(
                success=True,
                message=f"File '{file.filename}' uploaded successfully",
                doc_id=file.filename,
                document_count=document_count
            )
        else:
            return KnowledgeResponse(
                success=False,
                message=f"Failed to upload file '{file.filename}'"
            )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error uploading document: {str(e)}"
        )

@router.post("/directory", response_model=KnowledgeResponse)
async def add_documents_from_directory(
    directory_path: str,
    glob_pattern: str = "**/*.txt",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """Add documents from a directory to the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Check if directory exists
        if not os.path.exists(directory_path):
            return KnowledgeResponse(
                success=False,
                message=f"Directory '{directory_path}' does not exist"
            )
        
        # Add documents from directory
        success = await qdrant_manager.add_documents_from_directory(
            directory_path=directory_path,
            glob_pattern=glob_pattern,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if success:
            # Get collection info to return document count
            collection_info = await qdrant_manager.get_collection_info()
            document_count = collection_info.get("count", 0)
            
            return KnowledgeResponse(
                success=True,
                message=f"Documents from directory '{directory_path}' added successfully",
                document_count=document_count
            )
        else:
            return KnowledgeResponse(
                success=False,
                message=f"Failed to add documents from directory '{directory_path}'"
            )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error adding documents from directory: {str(e)}"
        )

@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(search_request: KnowledgeSearchRequest):
    """Search the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Search knowledge base
        results = await qdrant_manager.search_similar_documents(
            query=search_request.query,
            k=search_request.k,
            filter_metadata=search_request.filter_metadata
        )
        
        return KnowledgeSearchResponse(
            results=results,
            count=len(results)
        )
    except Exception as e:
        return KnowledgeSearchResponse(
            results=[],
            count=0
        )

@router.get("/collection", response_model=CollectionInfo)
async def get_collection_info():
    """Get information about the knowledge collection"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Get collection info
        info = await qdrant_manager.get_collection_info()
        
        if "error" in info:
            raise HTTPException(status_code=500, detail=info["error"])
        
        return CollectionInfo(
            name=info["name"],
            count=info["count"],
            metadata=info.get("metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection info: {str(e)}")

@router.get("/documents", response_model=DocumentList)
async def list_documents(limit: int = 100):
    """List documents in the knowledge collection"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # List documents
        documents = await qdrant_manager.list_documents(limit=limit)
        
        return DocumentList(
            documents=documents,
            count=len(documents)
        )
    except Exception as e:
        return DocumentList(
            documents=[],
            count=0
        )

@router.delete("/documents/{doc_id}", response_model=KnowledgeResponse)
async def delete_document(doc_id: str):
    """Delete a document from the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Delete document
        success = await qdrant_manager.delete_document_by_id(doc_id)
        
        if success:
            # Get collection info to return document count
            collection_info = await qdrant_manager.get_collection_info()
            document_count = collection_info.get("count", 0)
            
            return KnowledgeResponse(
                success=True,
                message=f"Document '{doc_id}' deleted successfully",
                document_count=document_count
            )
        else:
            return KnowledgeResponse(
                success=False,
                message=f"Failed to delete document '{doc_id}'"
            )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error deleting document: {str(e)}"
        )

@router.delete("/collection", response_model=KnowledgeResponse)
async def clear_collection():
    """Clear all documents from the knowledge collection"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Clear collection
        success = await qdrant_manager.clear_collection()
        
        if success:
            return KnowledgeResponse(
                success=True,
                message="Collection cleared successfully",
                document_count=0
            )
        else:
            return KnowledgeResponse(
                success=False,
                message="Failed to clear collection"
            )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error clearing collection: {str(e)}"
        )

@router.post("/directory/upload", response_model=KnowledgeResponse)
async def upload_directory(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None)
):
    """Upload multiple files as a directory to the knowledge base"""
    try:
        # Initialize Qdrant manager if not already initialized
        if not qdrant_manager._initialized:
            await qdrant_manager.initialize()
        
        # Parse metadata if provided
        base_metadata = {}
        if metadata:
            import json
            try:
                base_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                base_metadata = {"source": "uploaded_directory"}
        else:
            base_metadata = {"source": "uploaded_directory"}
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files to temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            
            # Add documents from directory
            success = await qdrant_manager.add_documents_from_directory(temp_dir)
            
            if success:
                # Get collection info to return document count
                collection_info = await qdrant_manager.get_collection_info()
                document_count = collection_info.get("count", 0)
                
                return KnowledgeResponse(
                    success=True,
                    message=f"Uploaded {len(files)} files successfully",
                    document_count=document_count
                )
            else:
                return KnowledgeResponse(
                    success=False,
                    message="Failed to upload directory"
                )
    except Exception as e:
        return KnowledgeResponse(
            success=False,
            message=f"Error uploading directory: {str(e)}"
        )