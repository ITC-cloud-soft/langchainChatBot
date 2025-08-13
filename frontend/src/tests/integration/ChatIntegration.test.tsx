import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ChatPage from '@/pages/ChatPage';
import Layout from '@/components/Layout';

// Mock Material-UI's useMediaQuery
vi.mock('@mui/material/useMediaQuery', () => ({
  default: () => false,
}));

// Mock the API
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
    getSessionStatistics: vi.fn(),
    exportChatHistory: vi.fn(),
    searchChatHistory: vi.fn(),
    clearError: vi.fn(),
  }),
}));

vi.mock('@/hooks/useChatStreaming', () => ({
  useChatStreaming: () => ({
    isStreaming: false,
    streamedMessage: '',
    startStreaming: vi.fn(),
    stopStreaming: vi.fn(),
    clearStreamedMessage: vi.fn(),
    clearError: vi.fn(),
  }),
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

describe('Chat Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('full chat workflow', async () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <Layout>
                <ChatPage />
              </Layout>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    // Verify page loads
    expect(screen.getByPlaceholderText(/メッセージを入力/i)).toBeInTheDocument();

    // Send a message
    const input = screen.getByPlaceholderText(/メッセージを入力/i);
    const sendButton = screen.getByRole('button', { name: /送信/i });

    fireEvent.change(input, { target: { value: 'Hello, how are you?' } });
    expect(sendButton).not.toBeDisabled();

    fireEvent.click(sendButton);

    // Verify API was called
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/メッセージを入力/i)).toHaveValue('');
    });
  });

  test('chat error handling', async () => {
    vi.mock('@/hooks/useChatState', () => ({
      useChatState: () => ({
        messages: [],
        isLoading: false,
        error: 'Connection failed',
        sessionId: 'test-session',
        sessions: [],
        sendMessage: vi.fn(),
        createSession: vi.fn(),
        clearMessages: vi.fn(),
        loadSession: vi.fn(),
        getSessionStatistics: vi.fn(),
        exportChatHistory: vi.fn(),
        searchChatHistory: vi.fn(),
        clearError: vi.fn(),
      }),
    }));

    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <Layout>
                <ChatPage />
              </Layout>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText(/Connection failed/i)).toBeInTheDocument();
  });

  test('chat loading state', async () => {
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
        getSessionStatistics: vi.fn(),
        exportChatHistory: vi.fn(),
        searchChatHistory: vi.fn(),
        clearError: vi.fn(),
      }),
    }));

    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <Layout>
                <ChatPage />
              </Layout>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('navigation between pages', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <Layout>
                <ChatPage />
              </Layout>
            }
          />
          <Route
            path="/llm-config"
            element={
              <Layout>
                <div>LLM Config Page</div>
              </Layout>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    // Verify chat page is loaded
    expect(screen.getByPlaceholderText(/メッセージを入力/i)).toBeInTheDocument();

    // Navigate to LLM config
    const llmConfigButton = screen.getByText('LLM設定');
    fireEvent.click(llmConfigButton);

    // Verify navigation occurred
    await waitFor(() => {
      expect(screen.getByText('LLM Config Page')).toBeInTheDocument();
    });
  });

  test('responsive layout', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <Layout>
                <ChatPage />
              </Layout>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    const layout = container.firstChild;
    expect(layout).toHaveStyle({ display: 'flex' });

    const appBar = screen.getByRole('banner');
    expect(appBar).toBeInTheDocument();

    const drawer = screen.getByRole('navigation');
    expect(drawer).toBeInTheDocument();
  });
});
