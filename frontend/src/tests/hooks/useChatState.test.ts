import { renderHook, act } from '@testing-library/react';
import { useChatState } from '@/hooks/useChatState';

describe('useChatState', () => {
  beforeEach(() => {
    // Clear any existing state
  });

  test('returns initial chat state', () => {
    const { result } = renderHook(() => useChatState());

    expect(result.current.state.messages).toEqual([]);
    expect(result.current.state.sessions).toEqual([]);
    expect(result.current.state.selectedSession).toBeNull();
    expect(result.current.state.sessionId).toBe('');
    expect(result.current.state.isLoading).toBe(false);
    expect(result.current.state.isSessionsLoading).toBe(false);
    expect(result.current.state.error).toBeNull();
  });

  test('provides state actions', () => {
    const { result } = renderHook(() => useChatState());

    expect(result.current.actions).toBeDefined();
    expect(typeof result.current.actions.setMessages).toBe('function');
    expect(typeof result.current.actions.addMessage).toBe('function');
    expect(typeof result.current.actions.updateLastMessage).toBe('function');
    expect(typeof result.current.actions.setSessions).toBe('function');
    expect(typeof result.current.actions.setSelectedSession).toBe('function');
    expect(typeof result.current.actions.setSessionId).toBe('function');
    expect(typeof result.current.actions.setLoading).toBe('function');
    expect(typeof result.current.actions.setSessionsLoading).toBe('function');
    expect(typeof result.current.actions.setError).toBe('function');
    expect(typeof result.current.actions.clearMessages).toBe('function');
    expect(typeof result.current.actions.resetState).toBe('function');
  });

  test('sets messages', () => {
    const { result } = renderHook(() => useChatState());

    const messages = [
      {
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date().toISOString(),
      },
      {
        role: 'assistant' as const,
        content: 'Hello there!',
        timestamp: new Date().toISOString(),
      },
    ];

    act(() => {
      result.current.actions.setMessages(messages);
    });

    expect(result.current.state.messages).toEqual(messages);
  });

  test('adds message', () => {
    const { result } = renderHook(() => useChatState());

    const message = {
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date().toISOString(),
    };

    act(() => {
      result.current.actions.addMessage(message);
    });

    expect(result.current.state.messages).toHaveLength(1);
    expect(result.current.state.messages[0]).toEqual(message);
  });

  test('updates last message', () => {
    const { result } = renderHook(() => useChatState());

    const initialMessage = {
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date().toISOString(),
    };

    act(() => {
      result.current.actions.addMessage(initialMessage);
    });

    const updates = {
      content: 'Hello world',
    };

    act(() => {
      result.current.actions.updateLastMessage(updates);
    });

    expect(result.current.state.messages[0].content).toBe('Hello world');
    expect(result.current.state.messages[0].role).toBe('user');
  });

  test('sets sessions', () => {
    const { result } = renderHook(() => useChatState());

    const sessions = [
      {
        session_id: 'session_123',
        title: 'Chat 1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        session_id: 'session_456',
        title: 'Chat 2',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    act(() => {
      result.current.actions.setSessions(sessions);
    });

    expect(result.current.state.sessions).toEqual(sessions);
  });

  test('sets selected session', () => {
    const { result } = renderHook(() => useChatState());

    const session = {
      session_id: 'session_123',
      title: 'Chat 1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    act(() => {
      result.current.actions.setSelectedSession(session);
    });

    expect(result.current.state.selectedSession).toEqual(session);
  });

  test('sets session id', () => {
    const { result } = renderHook(() => useChatState());

    act(() => {
      result.current.actions.setSessionId('session_123');
    });

    expect(result.current.state.sessionId).toBe('session_123');
  });

  test('sets loading state', () => {
    const { result } = renderHook(() => useChatState());

    act(() => {
      result.current.actions.setLoading(true);
    });

    expect(result.current.state.isLoading).toBe(true);

    act(() => {
      result.current.actions.setLoading(false);
    });

    expect(result.current.state.isLoading).toBe(false);
  });

  test('sets sessions loading state', () => {
    const { result } = renderHook(() => useChatState());

    act(() => {
      result.current.actions.setSessionsLoading(true);
    });

    expect(result.current.state.isSessionsLoading).toBe(true);

    act(() => {
      result.current.actions.setSessionsLoading(false);
    });

    expect(result.current.state.isSessionsLoading).toBe(false);
  });

  test('sets error state', () => {
    const { result } = renderHook(() => useChatState());

    act(() => {
      result.current.actions.setError('Test error');
    });

    expect(result.current.state.error).toBe('Test error');
    expect(result.current.state.isLoading).toBe(false);
    expect(result.current.state.isSessionsLoading).toBe(false);

    act(() => {
      result.current.actions.setError(null);
    });

    expect(result.current.state.error).toBeNull();
  });

  test('clears messages', () => {
    const { result } = renderHook(() => useChatState());

    const messages = [
      {
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date().toISOString(),
      },
    ];

    act(() => {
      result.current.actions.setMessages(messages);
    });

    expect(result.current.state.messages).toHaveLength(1);

    act(() => {
      result.current.actions.clearMessages();
    });

    expect(result.current.state.messages).toHaveLength(0);
  });

  test('resets state', () => {
    const { result } = renderHook(() => useChatState());

    const messages = [
      {
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date().toISOString(),
      },
    ];

    const sessions = [
      {
        session_id: 'session_123',
        title: 'Chat 1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    act(() => {
      result.current.actions.setMessages(messages);
      result.current.actions.setSessions(sessions);
      result.current.actions.setError('Test error');
      result.current.actions.setLoading(true);
    });

    expect(result.current.state.messages).toHaveLength(1);
    expect(result.current.state.sessions).toHaveLength(1);
    expect(result.current.state.error).toBe('Test error');
    expect(result.current.state.isLoading).toBe(true);

    act(() => {
      result.current.actions.resetState();
    });

    expect(result.current.state.messages).toHaveLength(0);
    expect(result.current.state.sessions).toHaveLength(0);
    expect(result.current.state.error).toBeNull();
    expect(result.current.state.isLoading).toBe(false);
    expect(result.current.state.sessionId).not.toBe('');
  });

  test('maintains state consistency across actions', () => {
    const { result } = renderHook(() => useChatState());

    const message = {
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date().toISOString(),
    };

    const session = {
      session_id: 'session_123',
      title: 'Chat 1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Perform multiple actions
    act(() => {
      result.current.actions.addMessage(message);
      result.current.actions.setSessions([session]);
      result.current.actions.setSelectedSession(session);
      result.current.actions.setSessionId('session_123');
      result.current.actions.setLoading(true);
    });

    expect(result.current.state.messages).toEqual([message]);
    expect(result.current.state.sessions).toEqual([session]);
    expect(result.current.state.selectedSession).toEqual(session);
    expect(result.current.state.sessionId).toBe('session_123');
    expect(result.current.state.isLoading).toBe(true);
  });
});
