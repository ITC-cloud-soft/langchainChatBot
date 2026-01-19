"""
サービスプロバイダー登録表

複数のサービスプロバイダーを管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from api.services.providers.base import ServiceProvider

logger = logging.getLogger("chatbot_app")


class ServiceProviderRegistry:
    """サービスプロバイダー登録表"""
    
    def __init__(self):
        """初期化"""
        self._providers: Dict[str, ServiceProvider] = {}
        
    def register(self, name: str, provider: ServiceProvider):
        """
        プロバイダーを登録
        
        Args:
            name: プロバイダー名
            provider: ServiceProviderインスタンス
        """
        self._providers[name] = provider
        logger.info(f"[Registry] Registered provider: {name}")
        
    def unregister(self, name: str):
        """
        プロバイダーを登録解除
        
        Args:
            name: プロバイダー名
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"[Registry] Unregistered provider: {name}")
        
    def get(self, name: str) -> Optional[ServiceProvider]:
        """
        プロバイダーを取得
        
        Args:
            name: プロバイダー名
            
        Returns:
            ServiceProviderインスタンスまたはNone
        """
        return self._providers.get(name)
    
    def get_all(self) -> Dict[str, ServiceProvider]:
        """すべてのプロバイダーを取得"""
        return self._providers.copy()
    
    def get_enabled_providers(self) -> Dict[str, ServiceProvider]:
        """有効なプロバイダーのみを取得"""
        return {
            name: provider 
            for name, provider in self._providers.items() 
            if provider.is_enabled()
        }
    
    async def get_all_tools(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        すべてのプロバイダーからツールを取得
        
        Args:
            context: コンテキスト情報
            
        Returns:
            {
                "provider_name": [tool1, tool2, ...],
                ...
            }
        """
        all_tools = {}
        
        for name, provider in self.get_enabled_providers().items():
            try:
                tools = await provider.get_tools(context)
                all_tools[name] = tools
                logger.info(f"[Registry] Got {len(tools)} tools from {name}")
            except Exception as e:
                logger.error(f"[Registry] Error getting tools from {name}: {str(e)}")
                all_tools[name] = []
        
        return all_tools
    
    async def get_all_function_schemas(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        すべてのプロバイダーからFunction Callingスキーマを取得
        
        Args:
            context: コンテキスト情報
            
        Returns:
            Function Callingスキーマのリスト
        """
        all_schemas = []
        
        all_tools = await self.get_all_tools(context)
        
        for name, tools in all_tools.items():
            provider = self._providers.get(name)
            if provider:
                try:
                    schemas = provider.to_function_schema(tools)
                    all_schemas.extend(schemas)
                    logger.info(f"[Registry] Got {len(schemas)} function schemas from {name}")
                except Exception as e:
                    logger.error(f"[Registry] Error getting function schemas from {name}: {str(e)}")
        
        return all_schemas
    
    async def get_all_react_prompts(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        すべてのプロバイダーからReActプロンプトを取得
        
        Args:
            context: コンテキスト情報
            
        Returns:
            統合されたReActプロンプト
        """
        all_prompts = []
        
        all_tools = await self.get_all_tools(context)
        
        for name, tools in all_tools.items():
            provider = self._providers.get(name)
            if provider:
                try:
                    prompt = provider.to_react_prompt(tools)
                    all_prompts.append(prompt)
                    logger.info(f"[Registry] Got ReAct prompt from {name}")
                except Exception as e:
                    logger.error(f"[Registry] Error getting ReAct prompt from {name}: {str(e)}")
        
        return "\n".join(all_prompts)
    
    def find_provider_by_tool_name(self, tool_name: str) -> Optional[ServiceProvider]:
        """
        ツール名からプロバイダーを特定
        
        Args:
            tool_name: ツール名 (例: "ars_flow_5")
            
        Returns:
            ServiceProviderインスタンスまたはNone
        """
        for provider in self.get_enabled_providers().values():
            if provider.parse_tool_call(tool_name) is not None:
                return provider
        
        return None
    
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ツールを実行
        
        Args:
            tool_name: ツール名
            parameters: パラメータ
            context: コンテキスト情報
            
        Returns:
            実行結果
        """
        provider = self.find_provider_by_tool_name(tool_name)
        
        if not provider:
            logger.error(f"[Registry] No provider found for tool: {tool_name}")
            return {
                "success": False,
                "error": f"No provider found for tool: {tool_name}"
            }
        
        tool_id = provider.parse_tool_call(tool_name)
        
        try:
            result = await provider.execute_tool(tool_id, parameters, context)
            return result
        except Exception as e:
            logger.error(f"[Registry] Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def count_providers(self) -> int:
        """登録されているプロバイダー数"""
        return len(self._providers)
    
    def count_enabled_providers(self) -> int:
        """有効なプロバイダー数"""
        return len(self.get_enabled_providers())
