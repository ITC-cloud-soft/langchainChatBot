import axios, { AxiosResponse, AxiosError } from 'axios';
import { logger } from '../utils/logger';

// API base URL - in development, this will be proxied to the backend
const API_BASE_URL = (import.meta as any).env.VITE_API_URL ?? 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10秒タイムアウト
});

// Request interceptor
api.interceptors.request.use(
  config => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  },
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Any status code within the range of 2xx causes this function to trigger
    return response;
  },
  (error: AxiosError) => {
    // Any status codes outside the range of 2xx cause this function to trigger
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status, data } = error.response;

      // Handle specific error status codes
      if (status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      } else if (status === 403) {
        // Forbidden - insufficient permissions
        logger.error('Forbidden: Insufficient permissions');
      } else if (status === 404) {
        // Not found
        logger.error('Not found:', error.config?.url);
      } else if (status === 422) {
        // Validation error - provide more detailed error message
        const errorMessage = (data as ErrorResponse)?.detail ?? '入力データの検証に失敗しました';
        logger.error('Validation error:', errorMessage);
        // Add custom error message for better user feedback
        error.message = errorMessage;
      } else if (status >= 500) {
        // Server error
        logger.error('Server error:', data);
      }
    } else if (error.request) {
      // The request was made but no response was received
      logger.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      logger.error('Request setup error:', error.message);
    }

    return Promise.reject(error);
  },
);

// エラーレスポンス型定義
interface ErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

// レスポンス型定義
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

// Chat API型定義
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  message_type?: 'text' | 'file' | 'error';
  source_documents?: Array<{
    content: string;
    metadata: Record<string, unknown>;
  }>;
  error_info?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

interface SendMessageResponse {
  response: string;
  session_id: string;
  timestamp: string;
}

interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
  total: number;
}

interface ClearChatHistoryResponse {
  session_id: string;
  deleted_messages: number;
}

// MySQL Chat History型定義
interface ChatSession {
  id: number;
  session_id: string;
  title?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
}

interface ChatSessionResponse {
  sessions: ChatSession[];
  total: number;
  page: number;
  per_page: number;
}

interface CreateSessionResponse {
  session_id: string;
  title?: string;
  created_at: string;
}

interface UpdateSessionResponse {
  session_id: string;
  title?: string;
  updated_at: string;
}


interface FullChatSessionResponse {
  session: ChatSession;
  messages: ChatMessage[];
  metadata?: {
    total_messages: number;
    total_tokens: number;
    last_user_message?: string;
    last_assistant_message?: string;
    model_used?: string;
    language: string;
    tags?: string[];
    custom_fields?: Record<string, unknown>;
  };
}


interface ChatSearchResponse {
  results: Array<{
    session: ChatSession;
    message: ChatMessage;
    rank: number;
    score: number;
  }>;
  total: number;
  page: number;
  per_page: number;
  query: string;
}

interface ChatExportResponse {
  session_id: string;
  export_format: 'json' | 'csv';
  data: string;
  exported_at: string;
}

interface ChatCleanupResponse {
  deleted_sessions: number;
  deleted_messages: number;
  freed_space: string;
}

// Chat API
export const chatApi = {
  sendMessage: async (message: string, sessionId?: string) => {
    const response = await api.post<ApiResponse<SendMessageResponse>>('/api/chat/send', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },

  streamMessage: async (message: string, sessionId?: string) => {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add auth token if available
        ...(localStorage.getItem('auth_token')
          ? { Authorization: `Bearer ${localStorage.getItem('auth_token')}` }
          : {}),
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    return {
      async *[Symbol.asyncIterator]() {
        if (!reader) return;

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') break;

                try {
                  const parsed = JSON.parse(data);
                  yield parsed;
                } catch (e) {
                  logger.error('Error parsing SSE data:', e);
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      },
    };
  },

  getChatHistory: async (sessionId: string) => {
    const response = await api.get<ApiResponse<ChatHistoryResponse>>(
      `/api/chat/sessions/${sessionId}/history`,
    );
    return response.data;
  },

  clearChatHistory: async (sessionId: string) => {
    const response = await api.delete<ApiResponse<ClearChatHistoryResponse>>(
      `/api/chat/sessions/${sessionId}`,
    );
    return response.data;
  },

  // MySQL Chat History API
  getSessions: async (page = 1, per_page = 20, user_id?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
    });
    if (user_id) {
      params.append('user_id', user_id);
    }

    const response = await api.get<ApiResponse<ChatSessionResponse>>(
      `/api/chat/sessions?${params.toString()}`,
    );
    return response.data;
  },

  createSession: async (title?: string, user_id?: string) => {
    const response = await api.post<ApiResponse<CreateSessionResponse>>('/api/chat/sessions', {
      title,
      user_id,
    });
    return response.data;
  },

  getSession: async (sessionId: string) => {
    const response = await api.get<ApiResponse<ChatSession>>(`/api/chat/sessions/${sessionId}`);
    return response.data;
  },

  updateSession: async (sessionId: string, title?: string, is_active?: boolean) => {
    const response = await api.put<ApiResponse<UpdateSessionResponse>>(
      `/api/chat/sessions/${sessionId}`,
      { title, is_active },
    );
    return response.data;
  },


  deleteSession: async (sessionId: string) => {
    const response = await api.delete<ApiResponse<{ success: boolean }>>(
      `/api/chat/sessions/${sessionId}/permanent`,
    );
    return response.data;
  },

  deleteAllSessions: async () => {
    const response = await api.delete<ApiResponse<{ deleted_sessions: number }>>(
      '/api/chat/sessions',
    );
    return response.data;
  },

  getFullSession: async (sessionId: string) => {
    const response = await api.get<FullChatSessionResponse>(`/api/chat/sessions/${sessionId}/full`);
    // バックエンドが直接データを返すので、ApiResponse形式に変換
    return {
      success: true,
      data: response.data,
      message: 'Session loaded successfully',
    };
  },

  searchChatHistory: async (
    query: string,
    page = 1,
    per_page = 20,
    user_id?: string,
    session_id?: string,
    start_date?: string,
    end_date?: string,
  ) => {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      per_page: per_page.toString(),
    });

    if (user_id) params.append('user_id', user_id);
    if (session_id) params.append('session_id', session_id);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);

    const response = await api.get<ApiResponse<ChatSearchResponse>>(
      `/api/chat/search?${params.toString()}`,
    );
    return response.data;
  },

  exportChatHistory: async (sessionId: string, format: 'json' | 'csv' = 'json') => {
    const response = await api.get<ApiResponse<ChatExportResponse>>(
      `/api/chat/sessions/${sessionId}/export`,
      { params: { format } },
    );
    return response.data;
  },

  cleanupChatHistory: async (days_old: number = 30) => {
    const response = await api.post<ApiResponse<ChatCleanupResponse>>('/api/chat/cleanup', {
      days_old,
    });
    return response.data;
  },
};

// LLM Configuration API
export const llmConfigApi = {
  getConfig: async () => {
    const response = await api.get('/api/llm/config');
    return response.data;
  },

  updateConfig: async (config: Record<string, unknown>) => {
    const response = await api.post('/api/llm/config', config);
    return response.data;
  },

  testConfig: async (config: Record<string, unknown>) => {
    const response = await api.post('/api/llm/config/test', config);
    return response.data;
  },

  getAvailableModels: async () => {
    const response = await api.get('/api/llm/models');
    return response.data;
  },

  refreshAvailableModels: async () => {
    const response = await api.post('/api/llm/models/refresh');
    return response.data;
  },

  getModelsFromApi: async (config: Record<string, unknown>) => {
    const response = await api.post('/api/llm/models/from-api', config);
    return response.data;
  },

  getDefaultConfig: async () => {
    const response = await api.get('/api/llm/config/default');
    return response.data;
  },

  resetConfig: async () => {
    const response = await api.post('/api/llm/config/reset');
    return response.data;
  },

  importConfig: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/llm/config/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  exportConfig: async () => {
    const response = await api.get('/api/llm/config/export');
    return response.data;
  },
};

// Embedding Configuration API
export const embeddingConfigApi = {
  getConfig: async () => {
    const response = await api.get('/api/embedding/config');
    return response.data;
  },

  updateConfig: async (config: Record<string, unknown>) => {
    const response = await api.post('/api/embedding/config', config);
    return response.data;
  },

  testConfig: async (config: Record<string, unknown>) => {
    const response = await api.post('/api/embedding/config/test', config);
    return response.data;
  },

  getAvailableModels: async () => {
    const response = await api.get('/api/embedding/models');
    return response.data;
  },

  getModelsForProvider: async (providerConfig: {
    provider: string;
    base_url?: string;
    api_key?: string;
  }) => {
    const response = await api.post('/api/embedding/models/for-provider', providerConfig);
    return response.data;
  },

  refreshAvailableModels: async () => {
    const response = await api.post('/api/embedding/models/refresh');
    return response.data;
  },

  getDefaultConfig: async () => {
    const response = await api.get('/api/embedding/config/default');
    return response.data;
  },

  resetConfig: async () => {
    const response = await api.post('/api/embedding/config/reset');
    return response.data;
  },
};

// Knowledge Management API
export const knowledgeApi = {
  addDocument: async (document: Record<string, unknown>) => {
    const response = await api.post('/api/knowledge/document', document);
    return response.data;
  },

  uploadDocument: async (file: File, metadata?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', metadata);
    }

    const response = await api.post('/api/knowledge/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  addDocumentsFromDirectory: async (directoryPath: string, options?: Record<string, unknown>) => {
    const response = await api.post('/api/knowledge/directory', {
      directory_path: directoryPath,
      ...options,
    });
    return response.data;
  },

  searchKnowledge: async (query: string, options?: Record<string, unknown>) => {
    const response = await api.post('/api/knowledge/search', {
      query,
      ...options,
    });
    return response.data;
  },

  getCollectionInfo: async () => {
    const response = await api.get('/api/knowledge/collection');
    return response.data;
  },

  listDocuments: async (limit?: number) => {
    const params = limit ? { limit } : {};
    const response = await api.get('/api/knowledge/documents', { params });
    return response.data;
  },

  deleteDocument: async (docId: string) => {
    const response = await api.delete(`/api/knowledge/documents/${docId}`);
    return response.data;
  },

  clearCollection: async () => {
    const response = await api.delete('/api/knowledge/collection');
    return response.data;
  },

  uploadDirectory: async (files: FileList, metadata?: string) => {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    if (metadata) {
      formData.append('metadata', metadata);
    }

    const response = await api.post('/api/knowledge/directory/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// System Health API
export const healthApi = {
  checkHealth: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },

  getServiceHealth: async (serviceName: string) => {
    const response = await api.get(`/api/health/${serviceName}`);
    return response.data;
  },
};

// Config Management API
export const configApi = {
  getConfig: async () => {
    const response = await api.get('/api/config');
    return response.data;
  },

  updateConfig: async (section: string, field: string, value: unknown) => {
    const response = await api.post('/api/config/update', {
      section,
      field,
      value,
    });
    return response.data;
  },

  getSections: async () => {
    const response = await api.get('/api/config/sections');
    return response.data;
  },

  getSection: async (section: string) => {
    const response = await api.get(`/api/config/section/${section}`);
    return response.data;
  },

  getChangeHistory: async (section?: string, field?: string, limit?: number) => {
    const params: Record<string, string | number> = {};
    if (section) params.section = section;
    if (field) params.field = field;
    if (limit) params.limit = limit;

    const response = await api.get('/api/config/history', { params });
    return response.data;
  },

  rollbackConfig: async (timestamp: number) => {
    const response = await api.post(`/api/config/rollback/${timestamp}`);
    return response.data;
  },

  exportConfig: async (exportPath: string, format = 'toml') => {
    const response = await api.post('/api/config/export', {
      export_path: exportPath,
      format,
    });
    return response.data;
  },

  importConfig: async (importPath: string, format = 'toml') => {
    const response = await api.post('/api/config/import', {
      import_path: importPath,
      format,
    });
    return response.data;
  },

  reloadConfig: async () => {
    const response = await api.post('/api/config/reload');
    return response.data;
  },

  resetConfig: async () => {
    const response = await api.post('/api/config/reset');
    return response.data;
  },

  validateConfig: async () => {
    const response = await api.get('/api/config/validate');
    return response.data;
  },
};

// Auth token management functions
export const setAuthToken = (token: string) => {
  localStorage.setItem('auth_token', token);
};

export const clearAuthToken = () => {
  localStorage.removeItem('auth_token');
};

export const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

export default api;
