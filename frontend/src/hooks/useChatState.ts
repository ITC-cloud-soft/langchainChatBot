import { useReducer, useCallback, useEffect } from 'react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceDocuments?: Array<{
    content: string;
    metadata: Record<string, unknown>;
  }>;
}

interface ChatSession {
  session_id: string;
  title?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  message_count?: number;
}

interface ChatState {
  messages: ChatMessage[];
  sessions: ChatSession[];
  selectedSession: ChatSession | null;
  sessionId: string;
  isLoading: boolean;
  isSessionsLoading: boolean;
  error: string | null;
}

type ChatAction =
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_LAST_MESSAGE'; payload: Partial<ChatMessage> }
  | { type: 'SET_SESSIONS'; payload: ChatSession[] }
  | { type: 'SET_SELECTED_SESSION'; payload: ChatSession | null }
  | { type: 'SET_SESSION_ID'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SESSIONS_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'RESET_STATE' };

const initialState: ChatState = {
  messages: [],
  sessions: [],
  selectedSession: null,
  sessionId: '',
  isLoading: false,
  isSessionsLoading: false,
  error: null,
};

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'SET_MESSAGES':
      return {
        ...state,
        messages: action.payload,
        error: null,
      };
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        error: null,
      };
    case 'UPDATE_LAST_MESSAGE':
      if (state.messages.length === 0) return state;

      const lastMessageIndex = state.messages.length - 1;
      const updatedMessages = [...state.messages];
      updatedMessages[lastMessageIndex] = {
        ...updatedMessages[lastMessageIndex],
        ...action.payload,
      };

      return {
        ...state,
        messages: updatedMessages,
      };
    case 'SET_SESSIONS':
      return {
        ...state,
        sessions: action.payload,
        isSessionsLoading: false,
        error: null,
      };
    case 'SET_SELECTED_SESSION':
      return {
        ...state,
        selectedSession: action.payload,
      };
    case 'SET_SESSION_ID':
      return {
        ...state,
        sessionId: action.payload,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_SESSIONS_LOADING':
      return {
        ...state,
        isSessionsLoading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        isSessionsLoading: false,
      };
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: [],
        error: null,
      };
    case 'RESET_STATE':
      return {
        ...initialState,
        sessionId: `session_${Date.now()}`,
      };
    default:
      return state;
  }
};

interface UseChatStateReturn {
  state: ChatState;
  actions: {
    setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
    addMessage: (message: ChatMessage) => void;
    updateLastMessage: (updates: Partial<ChatMessage>) => void;
    setSessions: (sessions: ChatSession[]) => void;
    setSelectedSession: (session: ChatSession | null) => void;
    setSessionId: (sessionId: string) => void;
    setLoading: (isLoading: boolean) => void;
    setSessionsLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
    clearMessages: () => void;
    resetState: () => void;
  };
}

export const useChatState = (): UseChatStateReturn => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const actions = {
    setMessages: useCallback((messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => {
      if (typeof messages === 'function') {
        const newMessages = messages(state.messages);
        dispatch({ type: 'SET_MESSAGES', payload: newMessages });
      } else {
        dispatch({ type: 'SET_MESSAGES', payload: messages });
      }
    }, [state.messages]),

    addMessage: useCallback((message: ChatMessage) => {
      dispatch({ type: 'ADD_MESSAGE', payload: message });
    }, []),

    updateLastMessage: useCallback((updates: Partial<ChatMessage>) => {
      dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: updates });
    }, []),

    setSessions: useCallback((sessions: ChatSession[]) => {
      dispatch({ type: 'SET_SESSIONS', payload: sessions });
    }, []),

    setSelectedSession: useCallback((session: ChatSession | null) => {
      dispatch({ type: 'SET_SELECTED_SESSION', payload: session });
    }, []),

    setSessionId: useCallback((sessionId: string) => {
      dispatch({ type: 'SET_SESSION_ID', payload: sessionId });
    }, []),

    setLoading: useCallback((isLoading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: isLoading });
    }, []),

    setSessionsLoading: useCallback((isLoading: boolean) => {
      dispatch({ type: 'SET_SESSIONS_LOADING', payload: isLoading });
    }, []),

    setError: useCallback((error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    }, []),

    clearMessages: useCallback(() => {
      dispatch({ type: 'CLEAR_MESSAGES' });
    }, []),

    resetState: useCallback(() => {
      dispatch({ type: 'RESET_STATE' });
    }, []),
  };

  return { state, actions };
};
