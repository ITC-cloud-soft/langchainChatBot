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
from api.core.qdrant_manager import qdrant_manager

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
    vector_db_recreated: bool = False
    old_dimension: int = None
    new_dimension: int = None


async def get_embedding_models_from_api(base_url: str, api_key: str = "", provider: str = "ollama") -> List[str]:
    """Get available embedding models from the specified API"""
    try:
        if provider == "ollama":
            # For Ollama, get available models
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # Try Ollama API
                ollama_url = f"{base_url.rstrip('/')}/api/tags"
                default_logger.info(f"Fetching Ollama embedding models from: {ollama_url}")
                
                try:
                    response = await client.get(ollama_url, headers=headers)
                    default_logger.info(f"Ollama API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        default_logger.info(f"Raw Ollama response: {data}")
                        default_logger.info(f"Found {len(models)} total models from Ollama")
                        
                        # Filter models that are suitable for embedding
                        embedding_models = []
                        for model in models:
                            name = model.get("name", "")
                            default_logger.debug(f"Checking model: {name}")
                            # More comprehensive embedding model detection
                            if any(keyword in name.lower() for keyword in ["embed", "bge", "minilm", "nomic", "mxbai", "snowflake", "arctic"]):
                                embedding_models.append(name)
                                default_logger.debug(f"Added embedding model: {name}")
                        
                        # If no specific embedding models found, return all models (user can choose)
                        if not embedding_models:
                            default_logger.info("No specific embedding models found, returning all models")
                            embedding_models = [model.get("name", "") for model in models if model.get("name")]
                        
                        default_logger.info(f"Filtered to {len(embedding_models)} embedding models: {embedding_models}")
                        return embedding_models
                    else:
                        default_logger.warning(f"Ollama API endpoint returned status {response.status_code}: {response.text}")
                        return []
                        
                except httpx.ConnectError as e:
                    default_logger.error(f"Connection error to Ollama at {ollama_url}: {e}")
                    return []
                except httpx.TimeoutException as e:
                    default_logger.error(f"Timeout error connecting to Ollama at {ollama_url}: {e}")
                    return []
                except Exception as e:
                    default_logger.error(f"Unexpected error connecting to Ollama: {e}")
                    return []
        
        elif provider == "openai":
            # For OpenAI, try to get models from API
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = {"Content-Type": "application/json"}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    
                    models_url = f"{base_url.rstrip('/')}/models"
                    default_logger.info(f"Fetching OpenAI embedding models from: {models_url}")
                    response = await client.get(models_url, headers=headers)
                    
                    default_logger.info(f"OpenAI API response status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("data", [])
                        default_logger.info(f"Found {len(models)} total models from OpenAI")
                        # Filter models that might be embedding models
                        embedding_models = []
                        for model in models:
                            model_id = model.get("id", "")
                            if any(keyword in model_id.lower() for keyword in ["embed", "text-embedding"]):
                                embedding_models.append(model_id)
                        
                        default_logger.info(f"Filtered to {len(embedding_models)} embedding models: {embedding_models}")
                        return embedding_models
                    else:
                        default_logger.warning(f"OpenAI API returned status {response.status_code}: {response.text}")
                        return []
            except Exception as e:
                default_logger.error(f"Error fetching OpenAI embedding models: {e}")
                return []
        
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
                    
                    return embedding_models if embedding_models else []
                else:
                    return []
    
    except Exception as e:
        default_logger.error(f"Error getting embedding models from API {base_url} (provider: {provider}): {e}")
        default_logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        default_logger.error(f"Traceback: {traceback.format_exc()}")
        return []

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
    # Get current dimension for comparison
    current_dimension = config_manager.get_value("embedding", "dimension") or 768
    
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
    
    # Check if dimension changed
    vector_db_recreated = False
    if current_dimension != config.dimension:
        default_logger.info(f"Embedding dimension changed from {current_dimension} to {config.dimension}")
        default_logger.warning("Vector database needs to be recreated due to dimension change")
        
        try:
            # Recreate vector database with new dimension
            success = await qdrant_manager.recreate_collection_with_new_dimension(config.dimension)
            if success:
                vector_db_recreated = True
                return ConfigStatus(
                    status="success",
                    message=f"Embedding configuration updated successfully. Vector database recreated with new dimension ({config.dimension}).",
                    vector_db_recreated=True,
                    old_dimension=current_dimension,
                    new_dimension=config.dimension
                )
            else:
                return ConfigStatus(
                    status="warning",
                    message=f"Embedding configuration updated but vector database recreation failed. Manual recreation may be required.",
                    vector_db_recreated=False,
                    old_dimension=current_dimension,
                    new_dimension=config.dimension
                )
        except Exception as e:
            default_logger.error(f"Error recreating vector database: {e}")
            return ConfigStatus(
                status="warning",
                message=f"Embedding configuration updated but vector database recreation failed: {str(e)}",
                vector_db_recreated=False,
                old_dimension=current_dimension,
                new_dimension=config.dimension
            )
    else:
        return ConfigStatus(
            status="success",
            message="Embedding configuration updated successfully"
        )

@router.post("/config/test", response_model=ConfigStatus)
async def test_embedding_config(config: EmbeddingConfig):
    """Test embedding configuration"""
    try:
        # Import here to avoid circular imports
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            from langchain_community.embeddings import OllamaEmbeddings
        
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            from langchain_community.embeddings import OpenAIEmbeddings
        
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

@router.post("/models/for-provider", response_model=List[str])
async def get_models_for_provider(request: Dict[str, Any]):
    """プロバイダー指定によるモデル取得"""
    try:
        provider = request.get("provider", "ollama")
        base_url = request.get("base_url", "")
        api_key = request.get("api_key", "")
        
        # プロバイダーに応じたデフォルトベースURLを設定
        if not base_url:
            if provider == "ollama":
                base_url = "http://localhost:11434"
            elif provider == "openai":
                base_url = "https://api.openai.com/v1"
            else:  # カスタム
                base_url = "http://localhost:11434/v1"
        
        default_logger.info(f"Getting models for provider: {provider}, Base URL: {base_url}")
        
        # 指定されたプロバイダーからモデルを取得
        models = await get_embedding_models_from_api(base_url, api_key, provider)
        
        default_logger.info(f"Models for provider {provider}: {models} (count: {len(models)})")
        
        return models
    except Exception as e:
        default_logger.error(f"Error getting models for provider: {e}")
        import traceback
        default_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting models for provider: {str(e)}")
    
@router.get("/models", response_model=List[str])
async def get_available_embedding_models():
    """Get list of available embedding models"""
    try:
        # Get current configuration
        provider = config_manager.get_value("embedding", "provider") or "ollama"
        base_url = config_manager.get_value("embedding", "base_url") or "http://localhost:11434"
        api_key = config_manager.get_value("embedding", "api_key") or ""
        
        default_logger.info(f"Getting available embedding models - Provider: {provider}, Base URL: {base_url}")
        
        # Get models from the configured API
        models = await get_embedding_models_from_api(base_url, api_key, provider)
        
        default_logger.info(f"Final models list for API response: {models} (count: {len(models)})")
        
        return models
    except Exception as e:
        default_logger.error(f"Error in get_available_embedding_models endpoint: {e}")
        import traceback
        default_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting available embedding models: {str(e)}")

@router.post("/models/refresh", response_model=List[str])
async def refresh_available_embedding_models():
    """Refresh list of available embedding models from the embedding API"""
    try:
        # Get current configuration
        provider = config_manager.get_value("embedding", "provider") or "ollama"
        base_url = config_manager.get_value("embedding", "base_url") or "http://localhost:11434"
        api_key = config_manager.get_value("embedding", "api_key") or ""
        
        default_logger.info(f"Refreshing available embedding models - Provider: {provider}, Base URL: {base_url}")
        
        # Get models from the configured API
        models = await get_embedding_models_from_api(base_url, api_key, provider)
        
        default_logger.info(f"Final refreshed models list for API response: {models} (count: {len(models)})")
        
        return models
    except Exception as e:
        default_logger.error(f"Error in refresh_available_embedding_models endpoint: {e}")
        import traceback
        default_logger.error(f"Traceback: {traceback.format_exc()}")
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