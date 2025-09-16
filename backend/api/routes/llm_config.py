"""
LLM Configuration API routes for the Chatbot System

This module provides API endpoints for managing LLM configurations.
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
class LLMConfig(BaseModel):
    """LLM configuration model"""
    provider: str = "openai"
    api_base: str
    api_key: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class LLMConfigResponse(BaseModel):
    """LLM configuration response model"""
    config: LLMConfig
    available_models: List[str]
    status: str

class ConfigStatus(BaseModel):
    """Configuration status model"""
    status: str
    message: str

# Global LLM configuration
current_llm_config = {
    "provider": "openai",
    "api_base": settings.OPENAI_API_BASE,
    "api_key": settings.OPENAI_API_KEY,
    "model_name": settings.OPENAI_MODEL_NAME,
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

async def get_models_from_api(api_base: str, api_key: str = "") -> List[str]:
    """Get available models from the specified API Base URL"""
    try:
        # Normalize API base URL
        api_base = api_base.rstrip('/')
        
        # Check provider based on API base URL and return appropriate models
        if "anthropic.com" in api_base:
            # Anthropic models - they don't have a public models endpoint
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022", 
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
        elif "openai.com" in api_base:
            # OpenAI models
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                models_url = f"{api_base}/models"
                response = await client.get(models_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    return [model["id"] for model in models if "id" in model]
                else:
                    # Fallback to common OpenAI models
                    return [
                        "gpt-4o",
                        "gpt-4o-mini", 
                        "gpt-4-turbo",
                        "gpt-4",
                        "gpt-3.5-turbo"
                    ]
        elif "generativelanguage.googleapis.com" in api_base:
            # Google Gemini models
            return [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro",
                "gemini-pro-vision"
            ]
        
        # For other APIs, try OpenAI-compatible endpoint first
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Set headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Try OpenAI-compatible models endpoint first
            # Handle the case where api_base already ends with /v1
            if api_base.endswith('/v1'):
                models_url = f"{api_base}/models"
            else:
                models_url = f"{api_base}/v1/models"
            
            response = await client.get(models_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                return [model["id"] for model in models if "id" in model]
            else:
                # Log detailed error information for debugging
                default_logger.warning(f"OpenAI API endpoint returned status {response.status_code} for {models_url}")
                if response.status_code != 401:
                    default_logger.warning(f"Response content: {response.text}")
            
            # If OpenAI endpoint fails, try Ollama API
            if "/v1" in api_base:
                ollama_base = api_base.replace("/v1", "")
            else:
                ollama_base = api_base
            
            ollama_url = f"{ollama_base}/api/tags"
            response = await client.get(ollama_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model["name"] for model in models]
            else:
                # Log detailed error information for debugging
                default_logger.warning(f"Ollama API endpoint returned status {response.status_code} for {ollama_url}")
                if response.status_code != 401:
                    default_logger.warning(f"Response content: {response.text}")
            
            # If both APIs fail, return empty list instead of fallback models
            default_logger.info(f"Both API endpoints failed for {api_base}, returning empty model list")
            return []
            
    except Exception as e:
        default_logger.error(f"Error getting models from API {api_base}: {e}")
        return []


@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config():
    """Get current LLM configuration"""
    # Get current configuration from config manager
    llm_config = {
        "provider": config_manager.get_value("llm", "provider") or "openai",
        "api_base": config_manager.get_value("llm", "api_base") or settings.OPENAI_API_BASE,
        "api_key": config_manager.get_value("llm", "api_key") or settings.OPENAI_API_KEY,
        "model_name": config_manager.get_value("llm", "model_name") or settings.OPENAI_MODEL_NAME,
        "temperature": config_manager.get_value("llm", "temperature") or settings.OPENAI_TEMPERATURE,
        "max_tokens": config_manager.get_value("llm", "max_tokens") or settings.OPENAI_MAX_TOKENS,
        "top_p": config_manager.get_value("llm", "top_p") or settings.OPENAI_TOP_P,
        "frequency_penalty": config_manager.get_value("llm", "frequency_penalty") or settings.OPENAI_FREQUENCY_PENALTY,
        "presence_penalty": config_manager.get_value("llm", "presence_penalty") or settings.OPENAI_PRESENCE_PENALTY
    }
    
    # Get available models from the configured API
    models = await get_models_from_api(llm_config["api_base"], llm_config["api_key"])
    
    return LLMConfigResponse(
        config=LLMConfig(**llm_config),
        available_models=models,
        status="active"
    )

@router.post("/config", response_model=ConfigStatus)
async def update_llm_config(config: LLMConfig):
    """Update LLM configuration"""
    # Update configuration using config manager
    result = config_manager.set_value("llm", "provider", config.provider)
    if not result.success:
        return ConfigStatus(
            status="error",
            message=result.message
        )
    
    config_manager.set_value("llm", "api_base", config.api_base)
    config_manager.set_value("llm", "api_key", config.api_key)
    config_manager.set_value("llm", "model_name", config.model_name)
    config_manager.set_value("llm", "temperature", config.temperature)
    config_manager.set_value("llm", "max_tokens", config.max_tokens)
    config_manager.set_value("llm", "top_p", config.top_p)
    config_manager.set_value("llm", "frequency_penalty", config.frequency_penalty)
    config_manager.set_value("llm", "presence_penalty", config.presence_penalty)
    
    # Update environment variables
    os.environ["OPENAI_API_BASE"] = config.api_base
    os.environ["OPENAI_API_KEY"] = config.api_key
    os.environ["OPENAI_MODEL_NAME"] = config.model_name
    os.environ["LLM_PROVIDER"] = config.provider
    
    # Reinitialize chat service LLM with new configuration
    try:
        from api.services.chat_service import chat_service
        if chat_service._initialized:
            await chat_service.reinitialize_llm()
            default_logger.info(f"Chat service LLM reinitialized with provider: {config.provider}")
    except Exception as e:
        default_logger.error(f"Error reinitializing chat service LLM: {e}")
        return ConfigStatus(
            status="warning",
            message=f"LLM configuration updated but chat service reinitialize failed: {str(e)}"
        )
    
    return ConfigStatus(
        status="success",
        message="LLM configuration updated successfully"
    )

@router.post("/config/test", response_model=ConfigStatus)
async def test_llm_config(config: LLMConfig):
    """Test LLM configuration"""
    try:
        # Import here to avoid circular imports
        from langchain_openai import ChatOpenAI
        
        # Create a test LLM instance
        test_llm = ChatOpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty
        )
        
        # Test with a simple prompt
        test_response = test_llm.invoke("Hello, this is a test.")
        
        if test_response:
            return ConfigStatus(
                status="success",
                message="LLM configuration test successful"
            )
        else:
            return ConfigStatus(
                status="error",
                message="LLM did not return a response"
            )
    except Exception as e:
        return ConfigStatus(
            status="error",
            message=f"LLM configuration test failed: {str(e)}"
        )

@router.get("/models", response_model=List[str])
async def get_available_models():
    """Get list of available models"""
    try:
        # Get current configuration
        api_base = config_manager.get_value("llm", "api_base") or settings.OPENAI_API_BASE
        api_key = config_manager.get_value("llm", "api_key") or settings.OPENAI_API_KEY
        
        # Get models from the configured API
        models = await get_models_from_api(api_base, api_key)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")


@router.post("/models/from-api", response_model=List[str])
async def get_models_from_api_endpoint(config: LLMConfig):
    """Get models from a specific API configuration"""
    try:
        models = await get_models_from_api(config.api_base, config.api_key)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models from API: {str(e)}")

@router.get("/config/default", response_model=LLMConfig)
async def get_default_config():
    """Get default LLM configuration"""
    return LLMConfig(
        provider=config_manager.get_value("llm", "provider") or "openai",
        api_base=config_manager.get_value("llm", "api_base") or settings.OPENAI_API_BASE,
        api_key=config_manager.get_value("llm", "api_key") or settings.OPENAI_API_KEY,
        model_name=config_manager.get_value("llm", "model_name") or settings.OPENAI_MODEL_NAME,
        temperature=config_manager.get_value("llm", "temperature") or 0.7,
        max_tokens=config_manager.get_value("llm", "max_tokens") or 1000,
        top_p=config_manager.get_value("llm", "top_p") or 1.0,
        frequency_penalty=config_manager.get_value("llm", "frequency_penalty") or 0.0,
        presence_penalty=config_manager.get_value("llm", "presence_penalty") or 0.0
    )

@router.post("/config/reset", response_model=ConfigStatus)
async def reset_llm_config():
    """Reset LLM configuration to defaults"""
    # Reset to default configuration
    success = config_manager.reset_to_defaults()
    
    if success:
        # Update environment variables
        os.environ["OPENAI_API_BASE"] = config_manager.get_value("llm", "api_base") or settings.OPENAI_API_BASE
        os.environ["OPENAI_API_KEY"] = config_manager.get_value("llm", "api_key") or settings.OPENAI_API_KEY
        os.environ["OPENAI_MODEL_NAME"] = config_manager.get_value("llm", "model_name") or settings.OPENAI_MODEL_NAME
        os.environ["LLM_PROVIDER"] = config_manager.get_value("llm", "provider") or "openai"
        
        return ConfigStatus(
            status="success",
            message="LLM configuration reset to defaults"
        )
    else:
        return ConfigStatus(
            status="error",
            message="Failed to reset LLM configuration"
        )

@router.post("/config/import", response_model=ConfigStatus)
async def import_llm_config(file: UploadFile = File(...)):
    """Import LLM configuration from a file"""
    try:
        # Read file content
        content = await file.read()
        
        # Parse JSON
        config_data = json.loads(content.decode("utf-8"))
        
        # Validate and update configuration
        config = LLMConfig(**config_data)
        
        # Update global configuration
        global current_llm_config
        current_llm_config = config.model_dump()
        
        # Update environment variables
        os.environ["OPENAI_API_BASE"] = config.api_base
        os.environ["OPENAI_API_KEY"] = config.api_key
        os.environ["OPENAI_MODEL_NAME"] = config.model_name
        os.environ["LLM_PROVIDER"] = config.provider
        
        return ConfigStatus(
            status="success",
            message="LLM configuration imported successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing LLM config: {str(e)}")

@router.get("/config/export")
async def export_llm_config():
    """Export current LLM configuration"""
    llm_section = config_manager.get_section("llm")
    if llm_section:
        return format_success_response(
            data=llm_section.model_dump(),
            message="LLM configuration exported successfully"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to export LLM configuration")

@router.post("/reinitialize", response_model=ConfigStatus)
async def reinitialize_chat_service():
    """Force reinitialize chat service with current LLM configuration"""
    try:
        from api.services.chat_service import chat_service
        success = await chat_service.reinitialize_llm()
        
        if success:
            return ConfigStatus(
                status="success",
                message="Chat service LLM reinitialized successfully"
            )
        else:
            return ConfigStatus(
                status="error",
                message="Failed to reinitialize chat service LLM"
            )
    except Exception as e:
        default_logger.error(f"Error reinitializing chat service: {e}")
        return ConfigStatus(
            status="error",
            message=f"Error reinitializing chat service: {str(e)}"
        )