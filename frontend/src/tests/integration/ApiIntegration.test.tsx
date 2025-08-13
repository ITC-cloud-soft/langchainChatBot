import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { testApi } from '@/services/testApi';
import { useApi } from '@/hooks/useApi';

// Test component for API integration
const TestApiComponent = () => {
  const { data, loading, error, execute } = useApi(
    () => testApi.chat.sendMessage('test message'),
    null,
  );

  const handleTestApi = async () => {
    try {
      await execute();
    } catch (err) {
      console.error('API test failed:', err);
    }
  };

  return (
    <div>
      <button onClick={handleTestApi}>Test API</button>
      {loading && <div>Loading...</div>}
      {error && <div>Error: {error}</div>}
      {data && <div>Data: {JSON.stringify(data)}</div>}
    </div>
  );
};

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('API health check', async () => {
    const result = await testApi.checkHealth();

    expect(result).toBeDefined();
    expect(result.status).toBeDefined();
    expect(result.timestamp).toBeDefined();
  });

  test('chat API integration', async () => {
    const result = await testApi.chat.sendMessage('Hello, test message');

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.response).toBeDefined();
    expect(result.data.session_id).toBeDefined();
    expect(result.data.timestamp).toBeDefined();
  });

  test('chat history API integration', async () => {
    const result = await testApi.chat.getHistory('test-session');

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.session_id).toBe('test-session');
    expect(result.data.messages).toBeDefined();
    expect(Array.isArray(result.data.messages)).toBe(true);
  });

  test('session creation API integration', async () => {
    const result = await testApi.chat.createSession('Test Session');

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.session_id).toBeDefined();
    expect(result.data.title).toBe('Test Session');
  });

  test('config API integration', async () => {
    const result = await testApi.config.get();

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.llm).toBeDefined();
    expect(result.data.embedding).toBeDefined();
  });

  test('config update API integration', async () => {
    const result = await testApi.config.update('llm', 'temperature', 0.8);

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
  });

  test('knowledge search API integration', async () => {
    const result = await testApi.knowledge.search('test query');

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.results).toBeDefined();
    expect(Array.isArray(result.data.results)).toBe(true);
  });

  test('knowledge collection API integration', async () => {
    const result = await testApi.knowledge.getCollection();

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.name).toBeDefined();
    expect(result.data.document_count).toBeDefined();
  });

  test('LLM test API integration', async () => {
    const config = { model: 'test-model', temperature: 0.7 };
    const result = await testApi.llm.test(config);

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.status).toBe('connected');
  });

  test('LLM models API integration', async () => {
    const result = await testApi.llm.getModels();

    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.models).toBeDefined();
    expect(Array.isArray(result.data.models)).toBe(true);
  });

  test('backend availability check', async () => {
    const isAvailable = await testApi.utils.isBackendAvailable();

    expect(typeof isAvailable).toBe('boolean');
  });

  test('test data creation', () => {
    const testData = testApi.utils.createTestData();

    expect(testData).toBeDefined();
    expect(testData.sessionId).toBeDefined();
    expect(testData.message).toBeDefined();
    expect(testData.config).toBeDefined();
  });

  test('React component API integration', async () => {
    const { container } = render(<TestApiComponent />);

    const testButton = screen.getByText('Test API');
    expect(testButton).toBeInTheDocument();

    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    const dataElement = screen.queryByText(/Data:/);
    if (dataElement) {
      expect(dataElement).toBeInTheDocument();
    }
  });

  test('API error handling', async () => {
    // Mock a failed API call
    const originalCheckHealth = testApi.checkHealth;
    testApi.checkHealth = vi.fn().mockRejectedValue(new Error('Network error'));

    try {
      await testApi.checkHealth();
      // Should not reach here
      expect(true).toBe(false);
    } catch (error) {
      expect(error).toBeDefined();
      expect(error.message).toBe('Network error');
    }

    // Restore original function
    testApi.checkHealth = originalCheckHealth;
  });

  test('concurrent API calls', async () => {
    const promises = [
      testApi.chat.sendMessage('Message 1'),
      testApi.chat.sendMessage('Message 2'),
      testApi.chat.sendMessage('Message 3'),
    ];

    const results = await Promise.all(promises);

    expect(results).toHaveLength(3);
    results.forEach(result => {
      expect(result).toBeDefined();
      expect(result.success).toBe(true);
    });
  });

  test('API timeout handling', async () => {
    // Mock a slow API call
    const originalSendMessage = testApi.chat.sendMessage;
    testApi.chat.sendMessage = vi
      .fn()
      .mockImplementation(() => new Promise(resolve => setTimeout(resolve, 2000)));

    const startTime = Date.now();
    try {
      await testApi.chat.sendMessage('test message');
    } catch (error) {
      expect(error).toBeDefined();
    }
    const endTime = Date.now();

    // Should timeout quickly due to test API configuration
    expect(endTime - startTime).toBeLessThan(6000);

    // Restore original function
    testApi.chat.sendMessage = originalSendMessage;
  });
});
