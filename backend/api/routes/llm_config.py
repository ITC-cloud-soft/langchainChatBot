"""
LLM Configuration API routes for the Chatbot System

This module provides API endpoints for managing LLM configurations.
"""

import os
import json
import httpx
from typing import Dict, Any, List, Annotated, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel

from api.core.config_manager import settings, config_manager
from api.core.utils import handle_exceptions, default_logger, format_success_response
from api.middleware import CurrentUser, get_current_admin_user, get_current_active_user, get_optional_user

# Create router
router = APIRouter()
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

class ModelInfo(BaseModel):
    """Model information with availability status"""
    name: str
    available: bool = True
    tier: str = "free"  # "free", "limited", "paid"
    description: str = ""

class LLMConfigResponse(BaseModel):
    """LLM configuration response model"""
    config: LLMConfig
    available_models: List[str]  # For backward compatibility
    models_info: List[ModelInfo] = []  # New structured model info
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

def classify_model_tier(model_name: str, provider: str = "") -> tuple[bool, str, str]:
    """Classify model tier and availability based on name and provider
    Returns: (available, tier, description)
    """
    model_lower = model_name.lower()
    
    # Gemini models classification
    if "gemini" in model_lower:
        if "2.5-pro" in model_lower or "2.0-pro" in model_lower:
            return (False, "paid", "高級モデル - 有料プランが必要")
        elif "1.5-pro" in model_lower and "latest" not in model_lower:
            return (True, "limited", "制限付き無料 - 1日50リクエスト")
        elif "1.5-flash" in model_lower:
            return (True, "free", "推奨 - 無料枠が大きい")
        elif "pro" in model_lower and "vision" not in model_lower:
            return (False, "deprecated", "非推奨 - 廃止されたモデル")
    
    # OpenAI models classification
    if "gpt" in model_lower:
        if "gpt-4" in model_lower and "turbo" not in model_lower and "mini" not in model_lower:
            return (True, "paid", "高性能 - 従量課金")
        elif "gpt-4o" in model_lower or "gpt-4-turbo" in model_lower:
            return (True, "paid", "最新モデル - 従量課金")
        elif "gpt-3.5" in model_lower:
            return (True, "free", "標準モデル")
    
    # Claude models classification
    if "claude" in model_lower:
        if "opus" in model_lower:
            return (True, "paid", "最高性能 - 従量課金")
        elif "sonnet" in model_lower:
            return (True, "paid", "バランス型 - 従量課金")
        elif "haiku" in model_lower:
            return (True, "free", "高速・低コスト")
    
    # Default: assume available
    return (True, "free", "")

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
            # Google Gemini models - try to fetch dynamically
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Gemini API uses API key as query parameter
                models_url = f"https://generativelanguage.googleapis.com/v1beta/models"
                params = {}
                if api_key:
                    params["key"] = api_key
                
                try:
                    response = await client.get(models_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        # Filter for generateContent-capable models and extract model names
                        model_names = []
                        for model in models:
                            model_name = model.get("name", "")
                            # Extract just the model ID (e.g., "models/gemini-1.5-flash" -> "gemini-1.5-flash")
                            if model_name.startswith("models/"):
                                model_id = model_name.replace("models/", "")
                                # Check if model supports generateContent
                                supported_methods = model.get("supportedGenerationMethods", [])
                                if "generateContent" in supported_methods:
                                    model_names.append(model_id)
                        
                        if model_names:
                            default_logger.info(f"Successfully fetched {len(model_names)} Gemini models from API")
                            return model_names
                    else:
                        default_logger.warning(f"Gemini API returned status {response.status_code}")
                except Exception as e:
                    default_logger.warning(f"Error fetching Gemini models: {e}")
                
                # Fallback to known models if API call fails
                default_logger.info("Using fallback Gemini model list")
                return [
                    "gemini-1.5-pro",
                    "gemini-1.5-flash",
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash-latest"
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
async def get_llm_config(
    current_user: Annotated[Optional[CurrentUser], Depends(get_optional_user)] = None
):
    """Get current LLM configuration (Optional authentication)"""
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
    
    # Create structured model info with availability status
    provider = llm_config["provider"]
    models_info = []
    for model_name in models:
        available, tier, description = classify_model_tier(model_name, provider)
        models_info.append(ModelInfo(
            name=model_name,
            available=available,
            tier=tier,
            description=description
        ))
    
    return LLMConfigResponse(
        config=LLMConfig(**llm_config),
        available_models=models,  # For backward compatibility
        models_info=models_info,
        status="active"
    )

@router.post("/config", response_model=ConfigStatus)
async def update_llm_config(
    config: LLMConfig,
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Update LLM configuration (Admin only)"""
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
async def test_llm_config(
    config: LLMConfig,
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Test LLM configuration (Admin only)"""
    try:
        # Create appropriate LLM instance based on provider
        if config.provider == "gemini":
            # Use native Gemini API
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            test_llm = ChatGoogleGenerativeAI(
                google_api_key=config.api_key,
                model=config.model_name,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p
            )
        elif config.provider == "anthropic":
            # Use native Anthropic API
            from langchain_anthropic import ChatAnthropic
            
            test_llm = ChatAnthropic(
                anthropic_api_key=config.api_key,
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p
            )
        else:
            # Use OpenAI-compatible API (openai, カスタム, etc.)
            from langchain_openai import ChatOpenAI
            
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
async def get_available_models(
    current_user: Annotated[Optional[CurrentUser], Depends(get_optional_user)] = None
):
    """Get list of available models (Authenticated users)"""
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
async def get_models_from_api_endpoint(
    config: LLMConfig,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """Get models from a specific API configuration (Authenticated users)"""
    try:
        models = await get_models_from_api(config.api_base, config.api_key)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models from API: {str(e)}")

@router.get("/config/default", response_model=LLMConfig)
async def get_default_config(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Get default LLM configuration (Admin only)"""
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
async def reset_llm_config(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Reset LLM configuration to defaults (Admin only)"""
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
async def import_llm_config(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)],
    file: UploadFile = File(...)
):
    """Import LLM configuration from a file (Admin only)"""
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
async def export_llm_config(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Export current LLM configuration (Admin only)"""
    llm_section = config_manager.get_section("llm")
    if llm_section:
        return format_success_response(
            data=llm_section.model_dump(),
            message="LLM configuration exported successfully"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to export LLM configuration")

@router.post("/reinitialize", response_model=ConfigStatus)
async def reinitialize_chat_service(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)]
):
    """Force reinitialize chat service with current LLM configuration (Admin only)"""
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