import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ChatPage from '@/pages/ChatPage';

// Mock the API and hooks
vi.mock('@/services/api', () => ({
  chatApi: {
    sendMessage: vi.fn().mockResolvedValue({
      success: true,
      data: {
        response: 'Test response',
        session_id: 'test-session',
        timestamp: new Date().toISOString(),
      },
    }),
    getHistory: vi.fn().mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session',
        messages: [],
        total: 0,
      },
    }),
    createSession: vi.fn().mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session',
        created_at: new Date().toISOString(),
      },
    }),
  },
}));

vi.mock('@/hooks/useChatState', () => ({
  useChatState: () => ({
    messages: [],
    isLoading: false,
    error: null,
    sessionId: 'test-session',
    sessions: [],
    sendMessage: vi.fn(),
    createSession: vi.fn(),
    clearMessages: vi.fn(),
    loadSession: vi.fn(),
  }),
}));

vi.mock('@/hooks/useChatStreaming', () => ({
  useChatStreaming: () => ({
    isStreaming: false,
    streamedMessage: '',
    startStreaming: vi.fn(),
    stopStreaming: vi.fn(),
  }),
}));

describe('ChatPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders chat interface', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText(/メッセージを入力/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /送信/i })).toBeInTheDocument();
  });

  test('handles message input', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    const input = screen.getByPlaceholderText(/メッセージを入力/i);
    fireEvent.change(input, { target: { value: 'Hello' } });

    expect(input).toHaveValue('Hello');
  });

  test('disables send button when input is empty', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    const sendButton = screen.getByRole('button', { name: /送信/i });
    expect(sendButton).toBeDisabled();
  });

  test('enables send button when input has text', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    const input = screen.getByPlaceholderText(/メッセージを入力/i);
    fireEvent.change(input, { target: { value: 'Hello' } });

    const sendButton = screen.getByRole('button', { name: /送信/i });
    expect(sendButton).not.toBeDisabled();
  });

  test('shows loading state when loading', () => {
    vi.mock('@/hooks/useChatState', () => ({
      useChatState: () => ({
        messages: [],
        isLoading: true,
        error: null,
        sessionId: 'test-session',
        sessions: [],
        sendMessage: vi.fn(),
        createSession: vi.fn(),
        clearMessages: vi.fn(),
        loadSession: vi.fn(),
      }),
    }));

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays error message when error occurs', () => {
    vi.mock('@/hooks/useChatState', () => ({
      useChatState: () => ({
        messages: [],
        isLoading: false,
        error: 'Test error',
        sessionId: 'test-session',
        sessions: [],
        sendMessage: vi.fn(),
        createSession: vi.fn(),
        clearMessages: vi.fn(),
        loadSession: vi.fn(),
      }),
    }));

    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/Test error/i)).toBeInTheDocument();
  });

  test('has proper accessibility attributes', () => {
    render(
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>,
    );

    const input = screen.getByPlaceholderText(/メッセージを入力/i);
    expect(input).toHaveAttribute('type', 'text');
    expect(input).toHaveAttribute('aria-label', expect.any(String));

    const sendButton = screen.getByRole('button', { name: /送信/i });
    expect(sendButton).toHaveAttribute('type', 'submit');
  });
});
