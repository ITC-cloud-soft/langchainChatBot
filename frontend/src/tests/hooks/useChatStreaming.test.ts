import { renderHook, act, waitFor } from '@testing-library/react';
import { useChatStreaming } from '@/hooks/useChatStreaming';
import { vi } from 'vitest';

// Mock dependencies
const mockChatApi = {
  streamMessage: vi.fn(),
};

vi.mock('@/services/api', () => ({
  chatApi: mockChatApi,
}));

vi.mock('@/utils/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
  },
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

describe('useChatStreaming', () => {
  const mockEnqueueSnackbar = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockEnqueueSnackbar.mockClear();
  });

  test('returns initial streaming state', () => {
    const { result } = renderHook(() => useChatStreaming());

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.streamedMessage).toBe('');
    expect(result.current.error).toBeNull();
  });

  test('starts streaming successfully', async () => {
    const mockStream = {
      async *[Symbol.asyncIterator]() {
        yield { content: 'Hello' };
        yield { content: ' World' };
        yield { done: true };
      },
    };
    mockChatApi.streamMessage.mockResolvedValue(mockStream);

    const { result } = renderHook(() => useChatStreaming());

    await act(async () => {
      await result.current.startStreaming('Hello', 'test-session');
    });

    expect(mockChatApi.streamMessage).toHaveBeenCalledWith('Hello', 'test-session');
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.streamedMessage).toBe('Hello World');
  });

  test('handles streaming errors', async () => {
    const mockError = new Error('Streaming failed');
    mockChatApi.streamMessage.mockRejectedValue(mockError);

    const { result } = renderHook(() => useChatStreaming());

    await act(async () => {
      await expect(result.current.startStreaming('Hello', 'test-session')).rejects.toThrow(
        'Streaming failed',
      );
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBe('Streaming failed');
  });

  test('stops streaming', () => {
    const { result } = renderHook(() => useChatStreaming());

    act(() => {
      result.current.stopStreaming();
    });

    expect(result.current.isStreaming).toBe(false);
  });

  test('clears streamed message', () => {
    const { result } = renderHook(() => useChatStreaming());

    act(() => {
      result.current.clearStreamedMessage();
    });

    expect(result.current.streamedMessage).toBe('');
  });

  test('clears streaming error', () => {
    const { result } = renderHook(() => useChatStreaming());

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  test('handles empty stream', async () => {
    const mockStream = {
      async *[Symbol.asyncIterator]() {
        // Empty stream
      },
    };
    mockChatApi.streamMessage.mockResolvedValue(mockStream);

    const { result } = renderHook(() => useChatStreaming());

    await act(async () => {
      await result.current.startStreaming('Hello', 'test-session');
    });

    expect(result.current.streamedMessage).toBe('');
  });

  test('handles stream with mixed content types', async () => {
    const mockStream = {
      async *[Symbol.asyncIterator]() {
        yield { content: 'Hello' };
        yield { data: 'World' };
        yield { content: '!' };
        yield { done: true };
      },
    };
    mockChatApi.streamMessage.mockResolvedValue(mockStream);

    const { result } = renderHook(() => useChatStreaming());

    await act(async () => {
      await result.current.startStreaming('Hello', 'test-session');
    });

    expect(result.current.streamedMessage).toBe('Hello!');
  });
});
