"""
戦略選択器

LLMの能力に基づいて、Function CallingまたはReAct解析のどちらを使用するか選択します。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("chatbot_app")


class StrategySelector:
    """戦略選択器"""
    
    STRATEGY_FUNCTION_CALLING = "function_calling"
    STRATEGY_REACT_PARSER = "react_parser"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書
                - strategy: "auto" | "function_calling" | "react_parser"
                - enable_fallback: bool (Function Calling失敗時にReActに降格)
        """
        self.config = config or {}
        self.forced_strategy = self.config.get("strategy", "auto")
        self.enable_fallback = self.config.get("enable_fallback", True)
        
    def select(self, capabilities: Dict[str, bool]) -> str:
        """
        実行戦略を選択
        
        Args:
            capabilities: LLMの能力情報
                {
                    "function_calling": bool,
                    "streaming": bool,
                    "tools": bool
                }
                
        Returns:
            "function_calling" または "react_parser"
        """
        # 強制戦略が設定されている場合
        if self.forced_strategy == self.STRATEGY_FUNCTION_CALLING:
            if capabilities.get("function_calling"):
                logger.info("[Strategy Selector] Using forced strategy: function_calling")
                return self.STRATEGY_FUNCTION_CALLING
            else:
                logger.warning("[Strategy Selector] Function calling forced but not supported, falling back to react_parser")
                return self.STRATEGY_REACT_PARSER
        
        if self.forced_strategy == self.STRATEGY_REACT_PARSER:
            logger.info("[Strategy Selector] Using forced strategy: react_parser")
            return self.STRATEGY_REACT_PARSER
        
        # 自動選択 (デフォルト)
        if capabilities.get("function_calling"):
            logger.info("[Strategy Selector] LLM supports Function Calling, using function_calling strategy")
            return self.STRATEGY_FUNCTION_CALLING
        else:
            logger.info("[Strategy Selector] LLM does not support Function Calling, using react_parser strategy")
            return self.STRATEGY_REACT_PARSER
    
    def should_fallback(self, error: Exception) -> bool:
        """
        エラー発生時にフォールバックすべきか判定
        
        Args:
            error: 発生したエラー
            
        Returns:
            フォールバックすべき場合True
        """
        if not self.enable_fallback:
            return False
        
        # Function Calling関連のエラーかチェック
        error_str = str(error).lower()
        fallback_keywords = [
            "function",
            "tool",
            "not supported",
            "invalid function",
            "function call failed"
        ]
        
        for keyword in fallback_keywords:
            if keyword in error_str:
                logger.info(f"[Strategy Selector] Fallback triggered by error: {error}")
                return True
        
        return False
    
    def get_strategy_name(self, strategy: str) -> str:
        """戦略の表示名を取得"""
        if strategy == self.STRATEGY_FUNCTION_CALLING:
            return "Function Calling"
        elif strategy == self.STRATEGY_REACT_PARSER:
            return "ReAct Parser"
        else:
            return "Unknown"
