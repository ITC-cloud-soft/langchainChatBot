import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LlmConfigPage from '@/pages/LlmConfigPage';

// Mock the API
vi.mock('@/services/api', () => ({
  llmConfigApi: {
    getConfig: vi.fn().mockResolvedValue({
      success: true,
      data: {
        provider: 'openai',
        api_base: 'https://api.openai.com/v1',
        api_key: '',
        model_name: 'gpt-3.5-turbo',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0,
      },
    }),
    updateConfig: vi.fn().mockResolvedValue({
      success: true,
      data: { message: 'Configuration updated' },
    }),
    testConfig: vi.fn().mockResolvedValue({
      success: true,
      data: { status: 'connected' },
    }),
    getAvailableModels: vi.fn().mockResolvedValue({
      success: true,
      data: { models: ['gpt-3.5-turbo', 'gpt-4'] },
    }),
  },
  embeddingConfigApi: {
    getConfig: vi.fn().mockResolvedValue({
      success: true,
      data: {
        provider: 'openai',
        model_name: 'text-embedding-ada-002',
      },
    }),
  },
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

describe('LlmConfigPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders LLM configuration page', async () => {
    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/LLM設定/i)).toBeInTheDocument();
    });
  });

  test('displays configuration form fields', async () => {
    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/プロバイダ/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/モデル名/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/温度/i)).toBeInTheDocument();
    });
  });

  test('handles form input changes', async () => {
    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const providerSelect = screen.getByLabelText(/プロバイダ/i);
      fireEvent.change(providerSelect, { target: { value: 'anthropic' } });
      expect(providerSelect).toHaveValue('anthropic');
    });
  });

  test('handles save configuration', async () => {
    const { enqueueSnackbar } = vi.mocked(require('notistack')).useSnackbar();

    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const saveButton = screen.getByRole('button', { name: /保存/i });
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(enqueueSnackbar).toHaveBeenCalledWith(
        expect.stringContaining('設定を保存しました'),
        expect.objectContaining({ variant: 'success' }),
      );
    });
  });

  test('handles test configuration', async () => {
    const { enqueueSnackbar } = vi.mocked(require('notistack')).useSnackbar();

    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const testButton = screen.getByRole('button', { name: /テスト/i });
      fireEvent.click(testButton);
    });

    await waitFor(() => {
      expect(enqueueSnackbar).toHaveBeenCalledWith(
        expect.stringContaining('接続テストに成功しました'),
        expect.objectContaining({ variant: 'success' }),
      );
    });
  });

  test('handles loading states', async () => {
    vi.mock('@/services/api', () => ({
      llmConfigApi: {
        getConfig: vi
          .fn()
          .mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000))),
        updateConfig: vi.fn().mockResolvedValue({ success: true }),
        testConfig: vi.fn().mockResolvedValue({ success: true }),
        getAvailableModels: vi.fn().mockResolvedValue({ success: true }),
      },
      embeddingConfigApi: {
        getConfig: vi.fn().mockResolvedValue({ success: true }),
      },
    }));

    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    }, 1500);
  });

  test('has proper accessibility attributes', async () => {
    render(
      <MemoryRouter>
        <LlmConfigPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const providerSelect = screen.getByLabelText(/プロバイダ/i);
      expect(providerSelect).toHaveAttribute('aria-label', expect.any(String));

      const saveButton = screen.getByRole('button', { name: /保存/i });
      expect(saveButton).toHaveAttribute('type', 'button');
    });
  });
});
