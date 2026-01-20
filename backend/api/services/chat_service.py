"""
Chat service for the Chatbot System

This module provides the core chat functionality, including message processing
and integration with LLM and knowledge base.
"""

import os
import uuid
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import Document

from api.core.qdrant_manager import qdrant_manager
from api.core.database import database_manager
from api.core.config_manager import settings, config_manager
from api.core.utils import handle_exceptions, default_logger
from api.services.base_service import BaseService
from api.services.chat_history_service import chat_history_service


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses"""
    
    def __init__(self):
        self.tokens = []
        self.yield_tokens = False
        self.llm_started = False
    
    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        """Called when LLM starts generating"""
        self.tokens = []
        self.yield_tokens = True
        self.llm_started = True
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM"""
        if self.yield_tokens and self.llm_started:
            self.tokens.append(token)
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating"""
        self.yield_tokens = False
        self.llm_started = False
    
    def get_tokens(self) -> List[str]:
        """Get accumulated tokens"""
        return self.tokens
    
    def clear_tokens(self) -> None:
        """Clear accumulated tokens"""
        self.tokens = []
        self.yield_tokens = False
        self.llm_started = False


class ChatService(BaseService):
    """Service for handling chat interactions"""
    
    def __init__(self):
        """Initialize chat service"""
        super().__init__(logger_name="chat_service")
        self.llm = None
        self.qa_chain = None
        self.chat_history = {}  # session_id -> history
        self._history_cache = {}  # session_id -> formatted_history cache
    
    async def initialize(self) -> bool:
        """Initialize chat service"""
        try:
            self.log_info("Initializing chat service")
            
            # Initialize Qdrant manager
            if not qdrant_manager._initialized:
                await qdrant_manager.initialize()
            
            # Initialize chat history service
            if not await chat_history_service.initialize():
                self.log_warning("Chat history service initialization failed, continuing with in-memory history")
            
            # Initialize LLM based on current configuration
            await self._initialize_llm()
            
            # Setup QA chain
            await self._setup_qa_chain()
            
            self._initialized = True
            self.log_info("Chat service initialized successfully")
            return True
        except Exception as e:
            self.log_error("Error initializing chat service", e)
            return False

    async def _initialize_llm(self):
        """Initialize LLM based on current configuration"""
        try:
            # Get current LLM configuration
            provider = settings.llm.provider if hasattr(settings, 'llm') else "openai"
            api_base = settings.llm.api_base if hasattr(settings, 'llm') else settings.OPENAI_API_BASE
            api_key = settings.llm.api_key if hasattr(settings, 'llm') else settings.OPENAI_API_KEY
            model_name = settings.llm.model_name if hasattr(settings, 'llm') else settings.OPENAI_MODEL_NAME
            temperature = settings.llm.temperature if hasattr(settings, 'llm') else 0.7
            
            # Debug: Log all configuration values
            self.log_info(f"Debug config values:")
            self.log_info(f"  provider from settings: {provider}")
            self.log_info(f"  api_base: {api_base}")
            self.log_info(f"  model_name: {model_name}")
            
            # Also check config_manager directly
            provider_from_config = config_manager.get_value("llm", "provider")
            self.log_info(f"  provider from config_manager: {provider_from_config}")
            
            # Use config_manager value if available
            if provider_from_config:
                provider = provider_from_config
                self.log_info(f"  Using provider from config_manager: {provider}")
            
            self.log_info(f"Initializing LLM with provider: {provider}, model: {model_name}, api_base: {api_base}")
            
            if provider == "gemini":
                self.log_info("Creating ChatGoogleGenerativeAI instance")
                self.llm = ChatGoogleGenerativeAI(
                    google_api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    streaming=True
                )
            elif provider == "anthropic":
                self.log_info("Creating ChatAnthropic instance")
                self.llm = ChatAnthropic(
                    anthropic_api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    streaming=True
                )
            elif provider == "openai":
                self.log_info("Creating ChatOpenAI instance")
                self.llm = ChatOpenAI(
                    base_url=api_base,
                    api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    streaming=True
                )
            else:
                # Default to OpenAI-compatible for other providers
                self.log_info(f"Creating ChatOpenAI instance for provider: {provider}")
                self.llm = ChatOpenAI(
                    base_url=api_base,
                    api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    streaming=True
                )
            
            self.log_info(f"LLM initialized successfully with provider: {provider}, type: {type(self.llm).__name__}")
            
        except Exception as e:
            self.log_error(f"Error initializing LLM with provider {provider}", e)
            # Fallback to OpenAI configuration
            self.llm = ChatOpenAI(
                base_url=settings.OPENAI_API_BASE,
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.7,
                streaming=True
            )
            self.log_warning("Fallback to OpenAI configuration")

    async def reinitialize_llm(self):
        """Reinitialize LLM with current configuration (called when config changes)"""
        try:
            self.log_info("Reinitializing LLM with updated configuration")
            await self._initialize_llm()
            await self._setup_qa_chain()
            self.log_info("LLM reinitialized successfully")
            return True
        except Exception as e:
            self.log_error("Error reinitializing LLM", e)
            return False

    def _get_prompt_template(self) -> str:
        """プロンプトテンプレートを取得"""
        return settings.chat.prompt_template
    
    def _get_max_history(self) -> int:
        """最大履歴数を取得"""
        return settings.chat.max_history
    
    def _get_user_label(self) -> str:
        """ユーザーラベルを取得"""
        return settings.chat.user_label
    
    def _get_assistant_label(self) -> str:
        """アシスタントラベルを取得"""
        return settings.chat.assistant_label
    
    def _create_qa_chain(self, llm, include_prompt: bool = True, system_prompt: str = None):
        """QAチェーンを作成"""
        if include_prompt:
            # カスタムシステムプロンプトが指定されている場合はそれを使用
            if system_prompt:
                # システムプロンプト内の波括弧をエスケープ（PromptTemplateが変数として解釈しないように）
                escaped_system_prompt = system_prompt.replace("{", "{{").replace("}", "}}")
                # システムプロンプトを既存のテンプレートに統合
                custom_template = f"{escaped_system_prompt}\n\n{self._get_prompt_template()}"
                prompt = PromptTemplate(
                    template=custom_template,
                    input_variables=["chat_history", "context", "question"]
                )
            else:
                prompt = PromptTemplate(
                    template=self._get_prompt_template(),
                    input_variables=["chat_history", "context", "question"]
                )
            
            # ConversationalRetrievalChainを使用して会話履歴をサポート
            return ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=qdrant_manager.vectorstore.as_retriever(),
                combine_docs_chain_kwargs={"prompt": prompt},
                return_source_documents=True,
                verbose=False
            )
        else:
            # プロンプトなしのシンプルなチェーン
            return ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=qdrant_manager.vectorstore.as_retriever(),
                return_source_documents=True,
                verbose=False
            )
    
    def _format_chat_history(self, session_id: str) -> str:
        """Format chat history for prompt inclusion"""
        if session_id not in self.chat_history:
            return ""
        
        # キャッシュをチェック
        if session_id in self._history_cache:
            return self._history_cache[session_id]
        
        history_text = ""
        # 直近のmax_history * 2 メッセージ（ユーザーとアシスタントのペア）を取得
        max_history = self._get_max_history()
        messages = self.chat_history[session_id][-max_history * 2:]
        
        user_label = self._get_user_label()
        assistant_label = self._get_assistant_label()
        
        for msg in messages:
            if msg["role"] == "user":
                history_text += f"{user_label}: {msg['content']}\n"
            else:
                history_text += f"{assistant_label}: {msg['content']}\n"
        
        formatted = history_text.strip()
        
        # キャッシュに保存
        self._history_cache[session_id] = formatted
        
        return formatted
    
    def _update_history_cache(self, session_id: str) -> None:
        """履歴キャッシュを更新"""
        if session_id in self._history_cache:
            del self._history_cache[session_id]
    
    async def _setup_qa_chain(self):
        """Setup RetrievalQA chain"""
        try:
            if not qdrant_manager._initialized or not qdrant_manager.vectorstore:
                self.log_warning("Vector store not initialized")
                return False
            
            # Create retrieval chain using helper method
            self.qa_chain = self._create_qa_chain(self.llm)
            
            self.log_info("QA chain setup successfully")
            return True
        except Exception as e:
            self.log_error("Error setting up QA chain", e)
            return False
    
    @handle_exceptions(default_logger)
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a chat message and return response"""
        self.ensure_initialized()
        
        # Validate message is not empty
        if not message or not message.strip():
            raise ValueError("Message must not be empty")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize chat history for session if not exists
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        
        # Add user message to history
        user_message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_history[session_id].append(user_message_data)
        
        # Save user message to database
        try:
            await chat_history_service.add_message(
                session_id=session_id,
                role="user",
                content=message,
                message_type="text"
            )
        except Exception as e:
            self.log_warning(f"Failed to save user message to database: {str(e)}")
        
        # Update cache
        self._update_history_cache(session_id)
        
        try:
            # Process message with QA chain
            if self.qa_chain:
                # Format chat history for ConversationalRetrievalChain
                # ConversationalRetrievalChainは (question, answer) のタプルリストを期待
                chat_history_pairs = []
                if session_id in self.chat_history:
                    messages = self.chat_history[session_id]
                    # 直近のメッセージペアを取得
                    for i in range(0, len(messages) - 2, 2):  # 最後のユーザーメッセージを除く
                        if i + 1 < len(messages):
                            if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                                chat_history_pairs.append((messages[i]["content"], messages[i + 1]["content"]))
                
                # システムプロンプトが指定されている場合は一時的なQAチェーンを作成
                if system_prompt:
                    temp_qa_chain = self._create_qa_chain(self.llm, include_prompt=True, system_prompt=system_prompt)
                    result = temp_qa_chain.invoke({
                        "question": message,
                        "chat_history": chat_history_pairs
                    })
                else:
                    result = self.qa_chain.invoke({
                        "question": message,
                        "chat_history": chat_history_pairs
                    })
                
                # Extract response and source documents
                self.log_debug(f"QA chain result type: {type(result)}")
                self.log_debug(f"QA chain result: {result}")
                
                # ConversationalRetrievalChain returns response in 'result' key
                if isinstance(result, dict):
                    response = result.get("answer", str(result))
                    source_documents = []
                    
                    # Extract source documents if available
                    if "source_documents" in result:
                        for doc in result["source_documents"]:
                            source_documents.append({
                                "content": doc.page_content,
                                "metadata": doc.metadata
                            })
                else:
                    # Handle unexpected response format
                    response = str(result)
                    source_documents = []
            else:
                # Fallback to simple knowledge search
                search_results = await qdrant_manager.search_similar_documents(message, k=3)
                
                if search_results:
                    response = search_results[0]["content"]
                    source_documents = [
                        {
                            "content": search_result["content"],
                            "metadata": search_result["metadata"]
                        }
                        for search_result in search_results
                    ]
                else:
                    response = "申し訳ありませんが、関連する情報が見つかりませんでした。"
                    source_documents = []
            
            # Add bot response to history
            assistant_message_data = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "source_documents": source_documents
            }
            self.chat_history[session_id].append(assistant_message_data)
            
            # Save assistant message to database
            try:
                await chat_history_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response,
                    message_type="text",
                    source_documents=source_documents
                )
            except Exception as e:
                self.log_warning(f"Failed to save assistant message to database: {str(e)}")
            
            # Update cache
            self._update_history_cache(session_id)
            
            self.log_info(f"Processed message for session {session_id}",
                          message_length=len(message),
                          response_length=len(response))
            
            return {
                "response": response,
                "source_documents": source_documents,
                "session_id": session_id
            }
        except Exception as e:
            self.log_error(f"Error processing message for session {session_id}", e)
            error_response = "申し訳ありませんが、メッセージの処理中にエラーが発生しました。"
            
            # Add error response to history
            error_message_data = {
                "role": "assistant",
                "content": error_response,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.chat_history[session_id].append(error_message_data)
            
            # Save error message to database
            try:
                await chat_history_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=error_response,
                    message_type="error",
                    error_info={"error": str(e)}
                )
            except Exception as db_error:
                self.log_warning(f"Failed to save error message to database: {str(db_error)}")
            
            # Update cache
            self._update_history_cache(session_id)
            
            return {
                "response": error_response,
                "source_documents": [],
                "session_id": session_id,
                "error": str(e)
            }
    
    async def stream_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        ars_token: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a chat response"""
        self.ensure_initialized()
        
        # Debug: Log current LLM type
        self.log_info(f"Stream message - LLM type: {type(self.llm).__name__}")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize chat history for session if not exists
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        
        # Add user message to history
        user_message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_history[session_id].append(user_message_data)
        
        # Save user message to database
        try:
            await chat_history_service.add_message(
                session_id=session_id,
                role="user",
                content=message,
                message_type="text"
            )
        except Exception as e:
            self.log_warning(f"Failed to save user message to database: {str(e)}")
        
        # Update cache
        self._update_history_cache(session_id)
        
        try:
            # Setup streaming callback
            callback = StreamingCallbackHandler()
            
            # Use the correctly initialized LLM instance with streaming callback
            # Clone the LLM with streaming enabled
            if hasattr(self.llm, 'model_copy'):
                # For Pydantic v2 models (newer langchain versions)
                streaming_llm = self.llm.model_copy(update={"streaming": True, "callbacks": [callback]})
            else:
                # Fallback: create new instance based on current LLM type
                from api.core.config_manager import config_manager
                provider = config_manager.get_value("llm", "provider") or "openai"
                api_base = config_manager.get_value("llm", "api_base") or settings.OPENAI_API_BASE
                api_key = config_manager.get_value("llm", "api_key") or settings.OPENAI_API_KEY
                model_name = config_manager.get_value("llm", "model_name") or settings.OPENAI_MODEL_NAME
                
                if provider == "anthropic":
                    streaming_llm = ChatAnthropic(
                        base_url=api_base,
                        api_key=api_key,
                        model=model_name,
                        temperature=0.7,
                        streaming=True,
                        callbacks=[callback]
                    )
                else:
                    streaming_llm = ChatOpenAI(
                        base_url=api_base,
                        api_key=api_key,
                        model=model_name,
                        temperature=0.7,
                        streaming=True,
                        callbacks=[callback]
                    )
            
            # Create temporary QA chain with streaming LLM
            if qdrant_manager._initialized and qdrant_manager.vectorstore:
                # Create QA chain using helper method
                qa_chain = self._create_qa_chain(streaming_llm, include_prompt=True, system_prompt=system_prompt)
                
                # Process message with streaming QA chain
                # Format chat history for ConversationalRetrievalChain
                chat_history_pairs = []
                if session_id in self.chat_history:
                    messages = self.chat_history[session_id]
                    # 直近のメッセージペアを取得
                    for i in range(0, len(messages) - 2, 2):  # 最後のユーザーメッセージを除く
                        if i + 1 < len(messages):
                            if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                                chat_history_pairs.append((messages[i]["content"], messages[i + 1]["content"]))
                
                result = qa_chain.invoke({
                    "question": message,
                    "chat_history": chat_history_pairs
                })
                
                # Get source documents
                source_documents = []
                if "source_documents" in result:
                    for doc in result["source_documents"]:
                        source_documents.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata
                        })
                
                # Stream tokens
                tokens = callback.get_tokens()
                full_response = "".join(tokens)
                self.log_info(f"Generated {len(tokens)} tokens, response: {full_response[:100]}...")
                
                # 表単メッセージのメタデータを初期化
                form_metadata = None
                
                # ReAct解析: 检测JSON格式的flow调用,返回参数表单
                if ars_token and full_response:
                    import re
                    
                    # 首先检查用户是否提交了Flow参数 (格式: EXECUTE_FLOW:flow_id:params_json)
                    param_submit_pattern = r'EXECUTE_FLOW:(\d+):(.+)'
                    param_match = re.search(param_submit_pattern, message)
                    
                    if param_match:
                        # 用户提交了参数,直接执行Flow
                        flow_id = param_match.group(1)
                        params_json = param_match.group(2)
                        
                        try:
                            params = json.loads(params_json)
                            self.log_info(f"[ARS REACT] User submitted params for flow {flow_id}: {params}")
                            
                            # 更新表単状態为 'submitted'
                            try:
                                # 查找最近的assistant消息（表単消息）
                                if session_id in self.chat_history:
                                    messages = self.chat_history[session_id]
                                    for msg in reversed(messages):
                                        if msg.get("role") == "assistant" and msg.get("message_id"):
                                            form_message_id = msg.get("message_id")
                                            
                                            from api.models.database import update_message_form_status_async
                                            from api.core.database import database_manager
                                            
                                            async with database_manager.get_session() as db_session:
                                                await update_message_form_status_async(
                                                    db=db_session,
                                                    message_id=form_message_id,
                                                    form_status='submitted',
                                                    form_data=params
                                                )
                                            self.log_info(f"Updated form status to 'submitted' for message {form_message_id}")
                                            break
                            except Exception as e:
                                self.log_warning(f"Failed to update form status: {str(e)}")
                            

                            from api.tools.ars_tools import ExecuteFlowTool
                            tool = ExecuteFlowTool(ars_token=ars_token)
                            result_str = await tool._arun(flow_id=flow_id, parameters=params)
                            result = json.loads(result_str)
                            
                            if result.get("success"):
                                # 格式化执行结果
                                result_data = result.get('result', {})
                                result_data_obj = result_data.get('result_data', {})
                                
                                # 构建美观的结果显示
                                formatted_result = f"✅ **Flow {flow_id} 実行成功!**\n\n"
                                
                                # 遍历result_data中的每个flow步骤
                                for flow_name, steps in result_data_obj.items():
                                    formatted_result += f"### 📋 {flow_name}\n\n"
                                    
                                    if isinstance(steps, list):
                                        for idx, step in enumerate(steps, 1):
                                            for step_name, step_data in step.items():
                                                status = step_data.get('result', 'unknown')
                                                
                                                if status == 'success':
                                                    formatted_result += f"**ステップ {idx}: {step_name}** ✅\n"
                                                    if 'data' in step_data:
                                                        formatted_result += f"- WorkID: `{step_data['data'].get('WorkID', 'N/A')}`\n"
                                                        formatted_result += f"- FK_Node: `{step_data['data'].get('FK_Node', 'N/A')}`\n"
                                                elif status == 'error':
                                                    formatted_result += f"**ステップ {idx}: {step_name}** ❌\n"
                                                    formatted_result += f"- エラーコード: `{step_data.get('msgcode', 'N/A')}`\n"
                                                    formatted_result += f"- エラーメッセージ: {step_data.get('messages', 'Unknown error')}\n"
                                                
                                                if 'ts' in step_data:
                                                    formatted_result += f"- 実行時刻: {step_data['ts']}\n"
                                                formatted_result += "\n"
                                
                                # 添加原始数据的折叠部分
                                formatted_result += "\n<details>\n<summary>📊 詳細データを表示</summary>\n\n"
                                formatted_result += f"```json\n{json.dumps(result_data, ensure_ascii=False, indent=2)}\n```\n"
                                formatted_result += "</details>"
                                
                                full_response = formatted_result
                            else:
                                full_response = f"❌ **Flow {flow_id}** 実行失敗: {result.get('error')}"
                        except Exception as e:
                            self.log_error(f"[ARS REACT] Error executing flow with params", e)
                            full_response = f"❌ パラメータ処理エラー: {str(e)}"
                    else:
                        # 检测JSON格式: {"id": "X", "type": "flow", "name": "..."}
                        # 只处理type为flow的情况,忽略tool类型
                        pattern = r'\{\s*"id"\s*:\s*"?(\d+)"?\s*,\s*"type"\s*:\s*"flow"'
                        match = re.search(pattern, full_response)
                    
                    if not param_match and match:
                        flow_id = match.group(1)
                        self.log_info(f"[ARS REACT] Detected flow ID {flow_id}, fetching params")
                        
                        try:
                            # 获取Flow的参数定义
                            from api.services.providers.ars_provider import ARSServiceProvider
                            import os
                            
                            ars_endpoint = os.getenv("ARS_API_ENDPOINT", "http://ars-backend:5001")
                            provider = ARSServiceProvider(api_endpoint=ars_endpoint)
                            provider.set_api_key(ars_token)
                            
                            context = {"ars_token": ars_token}
                            
                            # 获取Flow名称
                            flows = await provider.get_tools(context)
                            flow_name = None
                            for flow in flows:
                                if str(flow.get("id")) == str(flow_id):
                                    flow_name = flow.get("name")
                                    break
                            
                            # 获取参数定义
                            params_result = await provider.get_flow_params(flow_id, context)
                            
                            if params_result.get("success"):
                                params = params_result.get("params", [])
                                
                                if params:
                                    # 有参数需要填写,返回表单
                                    full_response = f"📋 **{flow_name or f'Flow {flow_id}'}** を実行します\n\n"
                                    full_response += "以下のパラメータを入力してください:\n\n"
                                    
                                    for param in params:
                                        param_name = param.get("api_param_name")
                                        param_type = param.get("param_type")
                                        
                                        full_response += f"- **{param_name}** ({param_type})"
                                        
                                        # オプション型の場合、選択肢を表示
                                        if param_type == "option" and param.get("option"):
                                            full_response += "\n  選択肢:\n"
                                            for opt in param["option"]:
                                                full_response += f"  - {opt['option_label']} ({opt['option_value']})\n"
                                        else:
                                            full_response += "\n"
                                    
                                    # メタデータとして flow_id と params を埋め込む
                                    full_response += f"\n---\n**Flow ID**: {flow_id}\n"
                                    full_response += "パラメータを入力後、再度送信してください。"
                                    
                                    # 表単メッセージのメタデータを設定（初期状態: pending）
                                    form_metadata = {
                                        "form_status": "pending",
                                        "flow_id": flow_id,
                                        "flow_name": flow_name
                                    }
                                    
                                    self.log_info(f"[ARS REACT] Returned param form for flow {flow_id}")
                                else:
                                    # パラメータ不要、直接実行
                                    from api.tools.ars_tools import ExecuteFlowTool
                                    tool = ExecuteFlowTool(ars_token=ars_token)
                                    result_str = await tool._arun(flow_id=flow_id)
                                    result = json.loads(result_str)
                                    
                                    if result.get("success"):
                                        full_response = f"✅ **{flow_name or f'Flow {flow_id}'}** 実行成功!\n\n実行結果:\n```json\n{json.dumps(result.get('result'), ensure_ascii=False, indent=2)}\n```"
                                    else:
                                        full_response = f"❌ **{flow_name or f'Flow {flow_id}'}** 実行失敗: {result.get('error')}"
                                    
                                    self.log_info(f"[ARS REACT] Flow {flow_id} executed (no params required)")
                            else:
                                full_response = f"❌ Flow {flow_id} のパラメータ取得に失敗しました: {params_result.get('error')}"
                            
                        except Exception as e:
                            self.log_error(f"[ARS REACT] Error processing flow {flow_id}", e)
                            full_response = f"❌ Flow {flow_id} の処理中にエラーが発生しました: {str(e)}"
                
                if full_response:
                    # トークンを1文字ずつストリーミング
                    for i, char in enumerate(full_response):
                        yield {
                            "type": "token",
                            "token": char,
                            "session_id": session_id,
                            "index": i
                        }
                else:
                    # トークンが生成されなかった場合のフォールバック
                    fallback_response = "応答が生成されませんでした。"
                    self.log_warning("No tokens generated, using fallback response")
                    for i, char in enumerate(fallback_response):
                        yield {
                            "type": "token",
                            "token": char,
                            "session_id": session_id,
                            "index": i
                        }
                    full_response = fallback_response
                
                # Save assistant message to database first to get message_id
                saved_message = None
                try:
                    # 表単メッセージの場合はmetadataを含める
                    self.log_info(f"Saving assistant message with metadata: {form_metadata}")
                    
                    saved_message = await chat_history_service.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        message_type="text",
                        source_documents=source_documents,
                        metadata=form_metadata
                    )
                    self.log_info(f"Saved message with ID: {saved_message.get('message_id') if saved_message else 'None'}")
                except Exception as e:
                    self.log_warning(f"Failed to save assistant message to database: {str(e)}")
                
                # Send final response with source documents and message_id
                yield {
                    "type": "final",
                    "response": full_response,
                    "source_documents": source_documents,
                    "session_id": session_id,
                    "message_id": saved_message.get("message_id") if saved_message else None,
                    "metadata": form_metadata
                }
                
                # Add bot response to history with message_id
                assistant_message_data = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                    "source_documents": source_documents,
                    "message_id": saved_message.get("message_id") if saved_message else None
                }
                self.chat_history[session_id].append(assistant_message_data)
                
                # Update cache
                self._update_history_cache(session_id)
            else:
                # Fallback to non-streaming response
                response = "申し訳ありませんが、現在ストリーミング応答を利用できません。"
                yield {
                    "type": "final",
                    "response": response,
                    "source_documents": [],
                    "session_id": session_id
                }
                
                # Add error response to history
                self.chat_history[session_id].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Streaming not available"
                })
                
                # Update cache
                self._update_history_cache(session_id)
        except Exception as e:
            self.log_error(f"Error streaming message for session {session_id}", e)
            error_response = "申し訳ありませんが、メッセージの処理中にエラーが発生しました。"
            
            yield {
                "type": "error",
                "response": error_response,
                "session_id": session_id,
                "error": str(e)
            }
            
            # Add error response to history
            error_message_data = {
                "role": "assistant",
                "content": error_response,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.chat_history[session_id].append(error_message_data)
            
            # Save error message to database
            try:
                await chat_history_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=error_response,
                    message_type="error",
                    error_info={"error": str(e)}
                )
            except Exception as db_error:
                self.log_warning(f"Failed to save error message to database: {str(db_error)}")
            
            # Update cache
            self._update_history_cache(session_id)
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        # First try to get from in-memory cache
        if session_id in self.chat_history:
            self.log_info(f"Retrieved chat history for session {session_id} from memory",
                          history_length=len(self.chat_history[session_id]))
            return self.chat_history[session_id]
        
        # Try to get from database
        try:
            session_data = await chat_history_service.get_session_history(session_id)
            if session_data and session_data.get("messages"):
                # Convert database messages to in-memory format
                messages = []
                for msg in session_data["messages"]:
                    message_data = {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"]
                    }
                    if msg.get("source_documents"):
                        message_data["source_documents"] = msg["source_documents"]
                    if msg.get("error_info"):
                        message_data["error"] = msg["error_info"]
                    messages.append(message_data)
                
                # Cache the result
                self.chat_history[session_id] = messages
                
                self.log_info(f"Retrieved chat history for session {session_id} from database",
                              history_length=len(messages))
                return messages
        except Exception as e:
            self.log_warning(f"Failed to retrieve chat history from database for session {session_id}: {str(e)}")
        
        self.log_warning(f"No chat history found for session {session_id}")
        return []
    
    async def clear_chat_history(self, session_id: str) -> bool:
        """Clear chat history for a session"""
        cleared_memory = False
        cleared_database = False
        
        # Clear from memory
        if session_id in self.chat_history:
            self.chat_history[session_id] = []
            cleared_memory = True
            self.log_info(f"Cleared chat history from memory for session {session_id}")
        
        # Clear from database
        try:
            success = await chat_history_service.delete_session(session_id)
            if success:
                cleared_database = True
                self.log_info(f"Cleared chat history from database for session {session_id}")
            else:
                self.log_warning(f"No chat history to clear from database for session {session_id}")
        except Exception as e:
            self.log_warning(f"Failed to clear chat history from database for session {session_id}: {str(e)}")
        
        return cleared_memory or cleared_database
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for chat service"""
        try:
            # Check if service is initialized
            if not self._initialized:
                return {
                    "status": "unhealthy",
                    "message": "Chat service is not initialized"
                }
            
            # Check LLM connection
            if self.llm is None:
                return {
                    "status": "unhealthy",
                    "message": "LLM is not initialized"
                }
            
            # Check QA chain
            if self.qa_chain is None:
                return {
                    "status": "degraded",
                    "message": "QA chain is not initialized"
                }
            
            # Check Qdrant manager
            if not qdrant_manager._initialized:
                return {
                    "status": "degraded",
                    "message": "Qdrant manager is not initialized"
                }
            
            # Check database connection
            try:
                db_health = await database_manager.health_check()
                if db_health["status"] != "healthy":
                    return {
                        "status": "degraded",
                        "message": f"Database connection issue: {db_health.get('message', 'Unknown error')}",
                        "database_health": db_health
                    }
            except Exception as db_error:
                return {
                    "status": "degraded",
                    "message": f"Database health check failed: {str(db_error)}"
                }
            
            return {
                "status": "healthy",
                "message": "Chat service is healthy",
                "active_sessions": len(self.chat_history),
                "database_health": db_health
            }
        except Exception as e:
            self.log_error("Error during health check", e)
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            }


# Global chat service instance
chat_service = ChatService()