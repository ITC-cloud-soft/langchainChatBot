"""
LLM能力検出器

LLMがFunction Callingをサポートしているかどうかを検出します。
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("chatbot_app")


class CapabilityDetector:
    """LLM能力検出器"""
    
    # Function Callingをサポートする既知のモデル
    FUNCTION_CALLING_MODELS = {
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4o",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3-5-sonnet",
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-ultra",
        "mistral-large",
        "command-r-plus"
    }
    
    def __init__(self, llm: Any):
        """
        初期化
        
        Args:
            llm: LangChainのLLMインスタンス
        """
        self.llm = llm
        
    def detect(self) -> Dict[str, bool]:
        """
        LLMの能力を検出
        
        Returns:
            {
                "function_calling": bool,  # Function Calling対応
                "streaming": bool,         # ストリーミング対応
                "tools": bool              # Tools API対応
            }
        """
        model_name = self._get_model_name()
        
        capabilities = {
            "function_calling": self._supports_function_calling(model_name),
            "streaming": self._supports_streaming(),
            "tools": self._supports_tools()
        }
        
        logger.info(f"[Capability Detector] Model: {model_name}, Capabilities: {capabilities}")
        return capabilities
    
    def _get_model_name(self) -> str:
        """モデル名を取得"""
        # LangChainの各LLMクラスからモデル名を取得
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name.lower()
        elif hasattr(self.llm, "model"):
            return self.llm.model.lower()
        elif hasattr(self.llm, "model_id"):
            return self.llm.model_id.lower()
        
        logger.warning("[Capability Detector] Could not determine model name")
        return "unknown"
    
    def _supports_function_calling(self, model_name: str) -> bool:
        """
        Function Callingをサポートしているか検出
        
        Args:
            model_name: モデル名
            
        Returns:
            サポートしている場合True
        """
        # 既知のモデルリストをチェック
        for supported_model in self.FUNCTION_CALLING_MODELS:
            if supported_model in model_name:
                logger.info(f"[Capability Detector] Model {model_name} supports Function Calling (known model)")
                return True
        
        # bind_toolsメソッドの存在をチェック
        if hasattr(self.llm, "bind_tools"):
            logger.info(f"[Capability Detector] Model {model_name} has bind_tools method")
            return True
        
        # bind_functionsメソッドの存在をチェック
        if hasattr(self.llm, "bind_functions"):
            logger.info(f"[Capability Detector] Model {model_name} has bind_functions method")
            return True
        
        logger.info(f"[Capability Detector] Model {model_name} does not support Function Calling")
        return False
    
    def _supports_streaming(self) -> bool:
        """ストリーミングをサポートしているか"""
        return hasattr(self.llm, "stream") or hasattr(self.llm, "astream")
    
    def _supports_tools(self) -> bool:
        """Tools APIをサポートしているか"""
        return hasattr(self.llm, "bind_tools")
    
    def get_provider_name(self) -> str:
        """プロバイダー名を取得"""
        class_name = self.llm.__class__.__name__
        
        if "OpenAI" in class_name:
            return "openai"
        elif "Anthropic" in class_name or "Claude" in class_name:
            return "anthropic"
        elif "Google" in class_name or "Gemini" in class_name:
            return "google"
        elif "Ollama" in class_name:
            return "ollama"
        else:
            return "unknown"
    
    def is_local_model(self) -> bool:
        """ローカルモデルかどうか"""
        provider = self.get_provider_name()
        return provider in ["ollama", "unknown"]
