"""
サービスプロバイダー基底クラス

すべてのサービスプロバイダーが実装すべきインターフェースを定義します。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("chatbot_app")


class ServiceProvider(ABC):
    """サービスプロバイダー基底クラス"""
    
    def __init__(self, name: str):
        """
        初期化
        
        Args:
            name: プロバイダー名
        """
        self.name = name
        self._enabled = True
        
    @abstractmethod
    async def get_tools(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        利用可能なツール一覧を取得
        
        Args:
            context: コンテキスト情報(認証トークンなど)
            
        Returns:
            ツール定義のリスト
            [
                {
                    "id": "tool_1",
                    "name": "ツール名",
                    "description": "説明",
                    "parameters": {...}
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    async def execute_tool(
        self, 
        tool_id: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ツールを実行
        
        Args:
            tool_id: ツールID
            parameters: 実行パラメータ
            context: コンテキスト情報
            
        Returns:
            実行結果
            {
                "success": bool,
                "result": Any,
                "error": str (失敗時)
            }
        """
        pass
    
    @abstractmethod
    def to_function_schema(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OpenAI Function Calling形式のスキーマに変換
        
        Args:
            tools: ツール定義リスト
            
        Returns:
            Function Calling用スキーマ
            [
                {
                    "name": "function_name",
                    "description": "説明",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def to_react_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        ReAct形式のプロンプトに変換
        
        Args:
            tools: ツール定義リスト
            
        Returns:
            ReAct用プロンプト文字列
        """
        pass
    
    def parse_tool_call(self, tool_name: str) -> Optional[str]:
        """
        Function Call名からツールIDを抽出
        
        Args:
            tool_name: Function Call名 (例: "ars_flow_5")
            
        Returns:
            ツールID (例: "5") またはNone
        """
        # デフォルト実装: プロバイダー名をプレフィックスとして使用
        prefix = f"{self.name.lower()}_"
        if tool_name.startswith(prefix):
            return tool_name[len(prefix):]
        return None
    
    def is_enabled(self) -> bool:
        """プロバイダーが有効かどうか"""
        return self._enabled
    
    def set_enabled(self, enabled: bool):
        """プロバイダーの有効/無効を設定"""
        self._enabled = enabled
        logger.info(f"Provider {self.name} {'enabled' if enabled else 'disabled'}")
    
    def get_name(self) -> str:
        """プロバイダー名を取得"""
        return self.name
    
    async def validate_context(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        コンテキストの検証(オプション)
        
        Args:
            context: コンテキスト情報
            
        Returns:
            検証結果
        """
        return True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', enabled={self._enabled})>"
