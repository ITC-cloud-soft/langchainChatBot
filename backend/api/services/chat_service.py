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
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import Document

from api.core.qdrant_manager import qdrant_manager
from api.core.database import database_manager
from api.core.config_manager import settings
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
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                base_url=settings.OPENAI_API_BASE,
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.7,
                streaming=True
            )
            
            # Setup QA chain
            await self._setup_qa_chain()
            
            self._initialized = True
            self.log_info("Chat service initialized successfully")
            return True
        except Exception as e:
            self.log_error("Error initializing chat service", e)
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
    
    def _create_qa_chain(self, llm, include_prompt: bool = True):
        """QAチェーンを作成"""
        if include_prompt:
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
        session_id: Optional[str] = None
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
                
                result = self.qa_chain.invoke({
                    "question": message,
                    "chat_history": chat_history_pairs
                })
                
                # Extract response and source documents
                self.log_debug(f"QA chain result type: {type(result)}")
                self.log_debug(f"QA chain result: {result}")
                
                # ConversationalRetrievalChain returns response in 'result' key
                if isinstance(result, dict):
                    response = result.get("result", str(result))
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
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a chat response"""
        self.ensure_initialized()
        
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
            
            # Create LLM with streaming callback
            streaming_llm = ChatOpenAI(
                base_url=settings.OPENAI_API_BASE,
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.7,
                streaming=True,
                callbacks=[callback]
            )
            
            # Create temporary QA chain with streaming LLM
            if qdrant_manager._initialized and qdrant_manager.vectorstore:
                # Create QA chain using helper method
                qa_chain = self._create_qa_chain(streaming_llm)
                
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
                
                # Send final response with source documents
                yield {
                    "type": "final",
                    "response": full_response,
                    "source_documents": source_documents,
                    "session_id": session_id
                }
                
                # Add bot response to history
                assistant_message_data = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                    "source_documents": source_documents
                }
                self.chat_history[session_id].append(assistant_message_data)
                
                # Save assistant message to database
                try:
                    await chat_history_service.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        message_type="text",
                        source_documents=source_documents
                    )
                except Exception as e:
                    self.log_warning(f"Failed to save assistant message to database: {str(e)}")
                
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