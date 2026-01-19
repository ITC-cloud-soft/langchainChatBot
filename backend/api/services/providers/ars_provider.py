"""
ARSサービスプロバイダー

ARS (Automated Request System) との統合を提供します。
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import ServiceProvider

logger = logging.getLogger("chatbot_app")


class ARSServiceProvider(ServiceProvider):
    """ARSサービスプロバイダー"""
    
    def __init__(self, api_endpoint: str):
        """
        初期化
        
        Args:
            api_endpoint: ARS APIエンドポイント
        """
        super().__init__("ARS")
        self.api_endpoint = api_endpoint
        self._flows_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5分
        self._api_key = None
        
    def set_api_key(self, api_key: str):
        """
        API Keyを設定
        
        Args:
            api_key: ARS API Key
        """
        self._api_key = api_key
        
    async def get_tools(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        ARSからFlow一覧を取得
        
        Args:
            context: {"api_key": "ars_xxx"} を含むコンテキスト
            
        Returns:
            Flow定義のリスト
        """
        # コンテキストからAPI Keyを取得
        api_key = None
        if context:
            api_key = context.get("api_key") or context.get("ars_token")
        
        if not api_key:
            api_key = self._api_key
            
        if not api_key:
            logger.warning("[ARS Provider] No API key available")
            return []
        
        # キャッシュチェック
        if self._is_cache_valid():
            logger.info("[ARS Provider] Using cached flows")
            return self._flows_cache
        
        # ARSからFlowsを取得
        try:
            url = f"{self.api_endpoint}/get_status"
            headers = {"X-API-Key": api_key}
            
            logger.info(f"[ARS Provider] Fetching flows from {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                flows = data.get("flows", [])
                
                # キャッシュ更新
                self._flows_cache = flows
                self._cache_timestamp = datetime.now()
                
                logger.info(f"[ARS Provider] Fetched {len(flows)} flows")
                return flows
                
        except Exception as e:
            logger.error(f"[ARS Provider] Error fetching flows: {str(e)}")
            # キャッシュがあれば返す
            if self._flows_cache:
                logger.info("[ARS Provider] Returning cached flows due to error")
                return self._flows_cache
            return []
    
    async def get_flow_params(
        self,
        flow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Flowの必要パラメータ定義を取得
        
        Args:
            flow_id: Flow ID
            context: {"api_key": "ars_xxx"} を含むコンテキスト
            
        Returns:
            パラメータ定義
            {
                "success": True,
                "flow_id": "5",
                "params": [
                    {
                        "api_param_name": "UserNo",
                        "param_type": "text",
                        "option": [...] (optional)
                    },
                    ...
                ]
            }
        """
        # コンテキストからAPI Keyを取得
        api_key = None
        if context:
            api_key = context.get("api_key") or context.get("ars_token")
        
        if not api_key:
            api_key = self._api_key
            
        if not api_key:
            return {
                "success": False,
                "error": "ARS API key not configured"
            }
        
        try:
            url = f"{self.api_endpoint}/get_param"
            headers = {"X-API-Key": api_key}
            params = {"id": flow_id, "type": "flow"}
            
            logger.info(f"[ARS Provider] Fetching params for flow {flow_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"[ARS Provider] Got {len(data.get('params', []))} params for flow {flow_id}")
                
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "params": data.get("params", [])
                }
                
        except Exception as e:
            logger.error(f"[ARS Provider] Error fetching params for flow {flow_id}: {str(e)}")
            return {
                "success": False,
                "flow_id": flow_id,
                "error": str(e)
            }
    
    async def execute_tool(
        self, 
        tool_id: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ARSのFlowを実行
        
        Args:
            tool_id: Flow ID (例: "5" または "flow_5")
            parameters: 実行パラメータ
            context: {"api_key": "ars_xxx"} を含むコンテキスト
            
        Returns:
            実行結果
        """
        # tool_idからflow_idを抽出
        flow_id = tool_id.replace("flow_", "")
        
        # コンテキストからAPI Keyを取得
        api_key = None
        if context:
            api_key = context.get("api_key") or context.get("ars_token")
        
        if not api_key:
            api_key = self._api_key
            
        if not api_key:
            return {
                "success": False,
                "error": "ARS API key not configured"
            }
        
        try:
            url = f"{self.api_endpoint}/execute"
            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "type": "flow",
                "id": int(flow_id),
                "params": parameters
            }
            
            logger.info(f"[ARS Provider] Executing flow {flow_id} with params: {parameters}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[ARS Provider] Flow {flow_id} executed successfully")
                    return {
                        "success": True,
                        "flow_id": flow_id,
                        "result": result.get("result_data", result)
                    }
                else:
                    # エラーレスポンスを解析
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", response.text)
                    except:
                        error_msg = response.text
                    
                    logger.error(f"[ARS Provider] Flow {flow_id} execution failed: {error_msg}")
                    return {
                        "success": False,
                        "flow_id": flow_id,
                        "error": error_msg
                    }
                    
        except Exception as e:
            logger.error(f"[ARS Provider] Error executing flow {flow_id}: {str(e)}")
            return {
                "success": False,
                "flow_id": flow_id,
                "error": str(e)
            }
    
    def to_function_schema(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OpenAI Function Calling形式のスキーマに変換
        
        Args:
            tools: Flow定義リスト
            
        Returns:
            Function Calling用スキーマ
        """
        schemas = []
        
        for flow in tools:
            # 非アクティブなFlowはスキップ
            if not flow.get("active", True):
                continue
            
            flow_id = flow.get("id")
            name = flow.get("name", f"Flow {flow_id}")
            description = flow.get("description", name)
            
            schema = {
                "name": f"ars_flow_{flow_id}",
                "description": f"{name}: {description}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "parameters": {
                            "type": "object",
                            "description": "Flowに渡すパラメータ(オプション)",
                            "additionalProperties": True
                        }
                    },
                    "required": []
                }
            }
            schemas.append(schema)
        
        logger.info(f"[ARS Provider] Generated {len(schemas)} function schemas")
        return schemas
    
    def to_react_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        ReAct形式のプロンプトに変換
        
        Args:
            tools: Flow定義リスト
            
        Returns:
            ReAct用プロンプト文字列
        """
        prompt = "\n## ARS利用可能フロー\n\n"
        
        active_flows = [f for f in tools if f.get("active", True)]
        
        if not active_flows:
            prompt += "現在利用可能なフローはありません。\n"
            return prompt
        
        for flow in active_flows:
            flow_id = flow.get("id")
            name = flow.get("name", f"Flow {flow_id}")
            description = flow.get("description", "")
            
            prompt += f"- **Flow {flow_id}**: {name}\n"
            if description:
                prompt += f"  説明: {description}\n"
        
        prompt += "\n### フロー実行方法\n\n"
        prompt += "フローを実行する場合は、以下のJSON形式で返してください:\n\n"
        prompt += "```json\n"
        prompt += '{\n'
        prompt += '  "provider": "ARS",\n'
        prompt += '  "type": "flow",\n'
        prompt += '  "id": <flow_id>,\n'
        prompt += '  "name": "<flow_name>",\n'
        prompt += '  "parameters": {}  // オプション\n'
        prompt += '}\n'
        prompt += "```\n\n"
        prompt += "**重要**: `type`は必ず`\"flow\"`を使用してください。\n"
        
        return prompt
    
    def parse_tool_call(self, tool_name: str) -> Optional[str]:
        """
        Function Call名からFlow IDを抽出
        
        Args:
            tool_name: Function Call名 (例: "ars_flow_5")
            
        Returns:
            Flow ID (例: "5")
        """
        if tool_name.startswith("ars_flow_"):
            return tool_name.replace("ars_flow_", "")
        return None
    
    async def validate_context(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        コンテキストの検証
        
        Args:
            context: コンテキスト情報
            
        Returns:
            API Keyが存在するかどうか
        """
        if not context:
            return self._api_key is not None
        
        api_key = context.get("api_key") or context.get("ars_token")
        return api_key is not None or self._api_key is not None
    
    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かどうか"""
        if not self._flows_cache or not self._cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._flows_cache = None
        self._cache_timestamp = None
        logger.info("[ARS Provider] Cache cleared")
