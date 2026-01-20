"""
ARS Tools for executing flows and interacting with ARS API

This module provides LangChain tools for executing ARS flows.
"""

import os
import json
import logging
import httpx
from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Get ARS endpoint from environment
ARS_API_ENDPOINT = os.getenv("ARS_API_ENDPOINT", "http://localhost:5050")


class ExecuteFlowInput(BaseModel):
    """Input schema for execute_flow tool"""
    flow_id: str = Field(..., description="The ID of the flow to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameters for the flow")


class ExecuteFlowTool(BaseTool):
    """Tool for executing ARS flows"""
    
    name: str = "execute_flow"
    description: str = """
    Execute an ARS flow by its ID.
    Use this tool when the user wants to execute or run a specific flow.
    Input should be the flow ID (e.g., "5" or "flow_5").
    Returns the execution result from the ARS system.
    """
    args_schema: type[BaseModel] = ExecuteFlowInput
    ars_token: Optional[str] = None
    
    def __init__(self, ars_token: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.ars_token = ars_token
    
    def _run(self, flow_id: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Execute the flow synchronously"""
        try:
            logger.info(f"[ARS TOOL] Executing flow {flow_id} with parameters: {parameters}")
            
            if not self.ars_token:
                logger.warning("[ARS TOOL] No ARS token available")
                return json.dumps({
                    "success": False,
                    "error": "ARS token not configured. Please configure ARS settings first."
                }, ensure_ascii=False)
            
            # Prepare request - ARS uses /execute endpoint with api_key header
            url = f"{ARS_API_ENDPOINT}/execute"
            headers = {
                "X-API-Key": self.ars_token,
                "Content-Type": "application/json"
            }
            # ARS execute endpoint expects: {"type": "flow", "id": flow_id, "params": {...}}
            payload = {
                "type": "flow",
                "id": int(flow_id),
                "params": parameters or {}
            }
            
            logger.info(f"[ARS TOOL] Calling ARS API: {url} with flow_id={flow_id}")
            
            # Make synchronous HTTP request
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                logger.info(f"[ARS TOOL] ARS API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[ARS TOOL] Flow executed successfully: {result}")
                    return json.dumps({
                        "success": True,
                        "flow_id": flow_id,
                        "result": result
                    }, ensure_ascii=False)
                else:
                    # Parse error response to avoid Unicode escape sequences
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", response.text)
                    except:
                        error_msg = response.text
                    
                    logger.error(f"[ARS TOOL] ARS API error: {response.status_code} - {error_msg}")
                    return json.dumps({
                        "success": False,
                        "flow_id": flow_id,
                        "error": error_msg
                    }, ensure_ascii=False)
                    
        except Exception as e:
            error_msg = f"Error executing flow: {str(e)}"
            logger.error(f"[ARS TOOL] {error_msg}", exc_info=True)
            return json.dumps({
                "success": False,
                "flow_id": flow_id,
                "error": error_msg
            }, ensure_ascii=False)
    
    async def _arun(self, flow_id: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Execute the flow asynchronously"""
        try:
            logger.info(f"[ARS TOOL] Async executing flow {flow_id} with parameters: {parameters}")
            
            if not self.ars_token:
                logger.warning("[ARS TOOL] No ARS token available")
                return json.dumps({
                    "success": False,
                    "error": "ARS token not configured. Please configure ARS settings first."
                }, ensure_ascii=False)
            
            # Prepare request - ARS uses /execute endpoint with api_key header
            url = f"{ARS_API_ENDPOINT}/execute"
            headers = {
                "X-API-Key": self.ars_token,
                "Content-Type": "application/json"
            }
            # ARS execute endpoint expects: {"type": "flow", "id": flow_id, "params": {...}}
            payload = {
                "type": "flow",
                "id": int(flow_id),
                "params": parameters or {}
            }
            
            logger.info(f"[ARS TOOL] Calling ARS API (async): {url} with flow_id={flow_id}")
            
            # Make asynchronous HTTP request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                logger.info(f"[ARS TOOL] ARS API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[ARS TOOL] Flow executed successfully: {result}")
                    return json.dumps({
                        "success": True,
                        "flow_id": flow_id,
                        "result": result
                    }, ensure_ascii=False)
                else:
                    # Parse error response to avoid Unicode escape sequences
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", response.text)
                    except:
                        error_msg = response.text
                    
                    logger.error(f"[ARS TOOL] ARS API error: {response.status_code} - {error_msg}")
                    return json.dumps({
                        "success": False,
                        "flow_id": flow_id,
                        "error": error_msg
                    }, ensure_ascii=False)
                    
        except Exception as e:
            error_msg = f"Error executing flow: {str(e)}"
            logger.error(f"[ARS TOOL] {error_msg}", exc_info=True)
            return json.dumps({
                "success": False,
                "flow_id": flow_id,
                "error": error_msg
            }, ensure_ascii=False)


def create_ars_tools(ars_token: Optional[str] = None):
    """Create ARS tools with the given token"""
    return [
        ExecuteFlowTool(ars_token=ars_token)
    ]
