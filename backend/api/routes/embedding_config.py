"""
Embedding Configuration API routes for the Chatbot System

This module provides API endpoints for managing embedding configurations.
"""

import os
import json
import httpx
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.core.config_manager import settings, config_manager
from api.core.utils import handle_exceptions, default_logger, format_success_response

# Create router
router = APIRouter()

# Pydantic models
class EmbeddingConfig(BaseModel):
    """Embedding configuration model"""
    provider: str = "ollama"
    base_url: str
    model_name: str
    api_key: str = ""
    dimension: int = 768

class EmbeddingConfigResponse(BaseModel):
    """Embedding configuration response model"""
    config: EmbeddingConfig
    available_models: List[str]
    status: str

class ConfigStatus(BaseModel):
    """Configuration status model"""
    status: str
    message: str

# Available embedding models by provider
EMBEDDING_MODELS = {
    "ollama": [
        "nomic-embed-text:latest",
        "nomic-embed-text:v1.5",
        "mxbai-embed-large:latest",
        "bge-large:latest",
        "all-minilm:latest"
    ],
    "openai": [
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002"
    ],
    "カスタム": []
}

async def get_embedding_models_from_api(base_url: str, api_key: str = "", provider: str = "ollama") -> List[str]:
    """Get available embedding models from the specified API"""
    try:
        if provider == "ollama":
            # For Ollama, get available models
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # Try Ollama API
                ollama_url = f"{base_url.rstrip('/')}/api/tags"
                response = await client.get(ollama_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    # Filter models that are suitable for embedding
                    embedding_models = []
                    for model in models:
                        name = model.get("name", "")
                        if any(keyword in name.lower() for keyword in ["embed", "bge", "minilm"]):
                            embedding_models.append(name)
                    
                    return embedding_models if embedding_models else EMBEDDING_MODELS["ollama"]
                else:
                    default_logger.warning(f"Ollama API endpoint returned status {response.status_code}")
                    return EMBEDDING_MODELS["ollama"]
        
        elif provider == "openai":
            # For OpenAI, return predefined models
            return EMBEDDING_MODELS["openai"]
        
        else:
            # For カスタム, try to get models
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                models_url = f"{base_url.rstrip('/')}/v1/models"
                response = await client.get(models_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    # Filter models that might be embedding models
                    embedding_models = []
                    for model in models:
                        model_id = model.get("id", "")
                        if any(keyword in model_id.lower() for keyword in ["embed", "text-embedding"]):
                            embedding_models.append(model_id)
                    
                    return embedding_models if embedding_models else ["custom-embedding-model"]
                else:
                    return ["custom-embedding-model"]
    
    except Exception as e:
        default_logger.error(f"Error getting embedding models from API {base_url}: {e}")
        return EMBEDDING_MODELS.get(provider, ["custom-embedding-model"])

@router.get("/config", response_model=EmbeddingConfigResponse)
async def get_embedding_config():
    """Get current embedding configuration"""
    # Get current configuration from config manager
    embedding_config = {
        "provider": config_manager.get_value("embedding", "provider") or "ollama",
        "base_url": config_manager.get_value("embedding", "base_url") or "http://localhost:11434",
        "model_name": config_manager.get_value("embedding", "model_name") or "nomic-embed-text:latest",
        "api_key": config_manager.get_value("embedding", "api_key") or "",
        "dimension": config_manager.get_value("embedding", "dimension") or 768
    }
    
    # Get available models from the configured API
    models = await get_embedding_models_from_api(
        embedding_config["base_url"], 
        embedding_config["api_key"], 
        embedding_config["provider"]
    )
    
    return EmbeddingConfigResponse(
        config=EmbeddingConfig(**embedding_config),
        available_models=models,
        status="active"
    )

@router.post("/config", response_model=ConfigStatus)
async def update_embedding_config(config: EmbeddingConfig):
    """Update embedding configuration"""
    # Update configuration using config manager
    result = config_manager.set_value("embedding", "provider", config.provider)
    if not result.success:
        return ConfigStatus(
            status="error",
            message=result.message
        )
    
    config_manager.set_value("embedding", "base_url", config.base_url)
    config_manager.set_value("embedding", "model_name", config.model_name)
    config_manager.set_value("embedding", "api_key", config.api_key)
    config_manager.set_value("embedding", "dimension", config.dimension)
    
    # Update environment variables
    os.environ["EMBEDDING_PROVIDER"] = config.provider
    os.environ["EMBEDDING_BASE_URL"] = config.base_url
    os.environ["EMBEDDING_MODEL_NAME"] = config.model_name
    os.environ["EMBEDDING_API_KEY"] = config.api_key
    os.environ["EMBEDDING_DIMENSION"] = str(config.dimension)
    
    return ConfigStatus(
        status="success",
        message="Embedding configuration updated successfully"
    )

@router.post("/config/test", response_model=ConfigStatus)
async def test_embedding_config(config: EmbeddingConfig):
    """Test embedding configuration"""
    try:
        # Import here to avoid circular imports
        from langchain.embeddings import OllamaEmbeddings
        from langchain.embeddings.openai import OpenAIEmbeddings
        
        # Create a test embedding instance based on provider
        if config.provider == "ollama":
            test_embedding = OllamaEmbeddings(
                model=config.model_name,
                base_url=config.base_url
            )
        elif config.provider == "openai":
            test_embedding = OpenAIEmbeddings(
                model=config.model_name,
                openai_api_key=config.api_key
            )
        else:
            # For カスタム, try OpenAIEmbeddings with custom base URL
            test_embedding = OpenAIEmbeddings(
                model=config.model_name,
                openai_api_key=config.api_key,
                openai_api_base=config.base_url
            )
        
        # Test with a simple text
        test_vector = test_embedding.embed_query("Hello, this is a test.")
        
        if test_vector and len(test_vector) > 0:
            # Check if dimension matches expected
            if len(test_vector) == config.dimension:
                return ConfigStatus(
                    status="success",
                    message=f"Embedding configuration test successful. Generated {len(test_vector)} dimensions."
                )
            else:
                return ConfigStatus(
                    status="warning",
                    message=f"Embedding configuration works but dimension mismatch. Expected {config.dimension}, got {len(test_vector)}"
                )
        else:
            return ConfigStatus(
                status="error",
                message="Embedding did not return a valid vector"
            )
    except Exception as e:
        return ConfigStatus(
            status="error",
            message=f"Embedding configuration test failed: {str(e)}"
        )

@router.get("/models", response_model=List[str])
async def get_available_embedding_models():
    """Get list of available embedding models"""
    try:
        # Get current configuration
        provider = config_manager.get_value("embedding", "provider") or "ollama"
        base_url = config_manager.get_value("embedding", "base_url") or "http://localhost:11434"
        api_key = config_manager.get_value("embedding", "api_key") or ""
        
        # Get models from the configured API
        models = await get_embedding_models_from_api(base_url, api_key, provider)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available embedding models: {str(e)}")

@router.post("/models/refresh", response_model=List[str])
async def refresh_available_embedding_models():
    """Refresh list of available embedding models from the embedding API"""
    try:
        # Get current configuration
        provider = config_manager.get_value("embedding", "provider") or "ollama"
        base_url = config_manager.get_value("embedding", "base_url") or "http://localhost:11434"
        api_key = config_manager.get_value("embedding", "api_key") or ""
        
        # Get models from the configured API
        models = await get_embedding_models_from_api(base_url, api_key, provider)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing available embedding models: {str(e)}")

@router.get("/config/default", response_model=EmbeddingConfig)
async def get_default_embedding_config():
    """Get default embedding configuration"""
    return EmbeddingConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model_name="nomic-embed-text:latest",
        api_key="",
        dimension=768
    )

@router.post("/config/reset", response_model=ConfigStatus)
async def reset_embedding_config():
    """Reset embedding configuration to defaults"""
    # Reset to default configuration
    success = config_manager.reset_to_defaults()
    
    if success:
        # Update environment variables
        os.environ["EMBEDDING_PROVIDER"] = config_manager.get_value("embedding", "provider") or "ollama"
        os.environ["EMBEDDING_BASE_URL"] = config_manager.get_value("embedding", "base_url") or "http://localhost:11434"
        os.environ["EMBEDDING_MODEL_NAME"] = config_manager.get_value("embedding", "model_name") or "nomic-embed-text:latest"
        os.environ["EMBEDDING_API_KEY"] = config_manager.get_value("embedding", "api_key") or ""
        os.environ["EMBEDDING_DIMENSION"] = str(config_manager.get_value("embedding", "dimension") or 768)
        
        return ConfigStatus(
            status="success",
            message="Embedding configuration reset to defaults"
        )
    else:
        return ConfigStatus(
            status="error",
            message="Failed to reset embedding configuration"
        )