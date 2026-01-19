"""
ARS Function Calling Service

このサービスは、ARSのFlowsを動的にLangChainのFunction Calling形式に変換します
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("chatbot_app")


class FlowExecutionInput(BaseModel):
    """Flow実行の入力パラメータ"""
    flow_id: int = Field(description="実行するFlowのID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Flowに渡すパラメータ（オプション）")


class ArsFlowFunction:
    """ARSのFlowをFunction Calling用に変換するクラス"""
    
    def __init__(self, flow_id: int, name: str, description: str, ars_token: str):
        self.flow_id = flow_id
        self.name = name
        self.description = description
        self.ars_token = ars_token
    
    async def execute(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Flowを実行
        
        Args:
            parameters: Flowに渡すパラメータ
            
        Returns:
            実行結果
        """
        from api.tools.ars_tools import ExecuteFlowTool
        
        try:
            tool = ExecuteFlowTool(ars_token=self.ars_token)
            result_str = await tool._arun(flow_id=str(self.flow_id))
            
            import json
            result = json.loads(result_str)
            
            return {
                "success": True,
                "flow_id": self.flow_id,
                "flow_name": self.name,
                "result": result.get("result"),
                "message": f"Flow {self.flow_id} ({self.name}) を正常に実行しました"
            }
        except Exception as e:
            logger.error(f"Flow {self.flow_id} の実行中にエラー: {str(e)}")
            return {
                "success": False,
                "flow_id": self.flow_id,
                "flow_name": self.name,
                "error": str(e),
                "message": f"Flow {self.flow_id} ({self.name}) の実行に失敗しました"
            }
    
    def to_langchain_tool(self) -> StructuredTool:
        """
        LangChainのStructuredToolに変換
        
        Returns:
            StructuredTool
        """
        async def execute_wrapper(parameters: Dict[str, Any] = None) -> str:
            result = await self.execute(parameters or {})
            import json
            return json.dumps(result, ensure_ascii=False)
        
        return StructuredTool(
            name=f"execute_flow_{self.flow_id}",
            description=f"{self.name}: {self.description}",
            func=execute_wrapper,
            coroutine=execute_wrapper
        )


class ArsFunctionService:
    """ARSのFlowsをFunction Calling用に管理するサービス"""
    
    @staticmethod
    async def fetch_flows_from_ars(
        api_key: str,
        endpoint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ARSからFlow一覧を取得
        
        Args:
            api_key: ARS API key
            endpoint: ARS API endpoint
            
        Returns:
            Flow一覧
        """
        from api.core.config import settings
        
        url = endpoint or f"{settings.ARS_API_ENDPOINT}/get_status"
        headers = {"X-API-Key": api_key}
        
        try:
            logger.info(f"Fetching flows from ARS: {url}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                flows = data.get("flows", [])
                
                logger.info(f"Fetched {len(flows)} flows from ARS")
                return flows
                
        except Exception as e:
            logger.error(f"Error fetching flows from ARS: {str(e)}")
            return []
    
    @staticmethod
    async def create_flow_functions(
        ars_token: str,
        endpoint: Optional[str] = None
    ) -> List[ArsFlowFunction]:
        """
        ARSからFlowsを取得し、Function Calling用の関数リストを作成
        
        Args:
            ars_token: ARS token
            endpoint: ARS API endpoint
            
        Returns:
            ArsFlowFunction のリスト
        """
        flows = await ArsFunctionService.fetch_flows_from_ars(ars_token, endpoint)
        
        flow_functions = []
        for flow in flows:
            # activeなflowのみを対象
            if not flow.get("active", True):
                continue
            
            flow_id = flow.get("id")
            name = flow.get("name", f"Flow {flow_id}")
            description = flow.get("description", name)
            
            flow_function = ArsFlowFunction(
                flow_id=flow_id,
                name=name,
                description=description,
                ars_token=ars_token
            )
            flow_functions.append(flow_function)
        
        logger.info(f"Created {len(flow_functions)} flow functions")
        return flow_functions
    
    @staticmethod
    async def create_langchain_tools(
        ars_token: str,
        endpoint: Optional[str] = None
    ) -> List[StructuredTool]:
        """
        LangChainのtoolsリストを作成
        
        Args:
            ars_token: ARS token
            endpoint: ARS API endpoint
            
        Returns:
            StructuredTool のリスト
        """
        flow_functions = await ArsFunctionService.create_flow_functions(ars_token, endpoint)
        tools = [func.to_langchain_tool() for func in flow_functions]
        
        logger.info(f"Created {len(tools)} LangChain tools")
        return tools
    
    @staticmethod
    def create_function_definitions(flows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OpenAI Function Calling形式の関数定義を作成
        
        Args:
            flows: Flow一覧
            
        Returns:
            関数定義のリスト
        """
        functions = []
        
        for flow in flows:
            if not flow.get("active", True):
                continue
            
            flow_id = flow.get("id")
            name = flow.get("name", f"Flow {flow_id}")
            description = flow.get("description", name)
            
            function_def = {
                "name": f"execute_flow_{flow_id}",
                "description": f"{name}: {description}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "flow_id": {
                            "type": "integer",
                            "description": f"Flow ID (固定値: {flow_id})"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Flowに渡すパラメータ（オプション）"
                        }
                    },
                    "required": ["flow_id"]
                }
            }
            functions.append(function_def)
        
        return functions
