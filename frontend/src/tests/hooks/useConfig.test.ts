import { renderHook, act, waitFor } from '@testing-library/react';
import { useConfig } from '@/hooks/useConfig';
import { vi } from 'vitest';

// Mock dependencies
const mockConfigApi = {
  getConfig: vi.fn(),
  updateConfig: vi.fn(),
  getSections: vi.fn(),
  getSection: vi.fn(),
  getChangeHistory: vi.fn(),
  rollbackConfig: vi.fn(),
  exportConfig: vi.fn(),
  importConfig: vi.fn(),
  reloadConfig: vi.fn(),
  resetConfig: vi.fn(),
  validateConfig: vi.fn(),
};

vi.mock('@/services/api', () => ({
  configApi: mockConfigApi,
}));

vi.mock('@/hooks/useApi', () => ({
  useLocalStorage: () => [{ theme: 'light', language: 'ja' }, vi.fn()],
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

describe('useConfig', () => {
  const mockEnqueueSnackbar = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockEnqueueSnackbar.mockClear();
  });

  test('returns initial config state', () => {
    const { result } = renderHook(() => useConfig());

    expect(result.current.config).toEqual({ theme: 'light', language: 'ja' });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('fetches config successfully', async () => {
    const mockResponse = { success: true, data: { theme: 'dark', language: 'en' } };
    mockConfigApi.getConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.fetchConfig();
      expect(response).toEqual(mockResponse);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('handles config fetch errors', async () => {
    const mockError = new Error('Failed to fetch config');
    mockConfigApi.getConfig.mockRejectedValue(mockError);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      await expect(result.current.fetchConfig()).rejects.toThrow('Failed to fetch config');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('Failed to fetch config');
  });

  test('updates config successfully', async () => {
    const mockResponse = { success: true, data: { theme: 'dark' } };
    mockConfigApi.updateConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.updateConfig('ui', 'theme', 'dark');
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.updateConfig).toHaveBeenCalledWith('ui', 'theme', 'dark');
    expect(result.current.isLoading).toBe(false);
  });

  test('handles config update errors', async () => {
    const mockError = new Error('Failed to update config');
    mockConfigApi.updateConfig.mockRejectedValue(mockError);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      await expect(result.current.updateConfig('ui', 'theme', 'dark')).rejects.toThrow(
        'Failed to update config',
      );
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('Failed to update config');
  });

  test('gets config sections', async () => {
    const mockSections = ['ui', 'llm', 'embedding'];
    mockConfigApi.getSections.mockResolvedValue({ success: true, data: mockSections });

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const sections = await result.current.getSections();
      expect(sections).toEqual(mockSections);
    });

    expect(mockConfigApi.getSections).toHaveBeenCalled();
  });

  test('gets specific config section', async () => {
    const mockSection = { theme: 'dark', language: 'en' };
    mockConfigApi.getSection.mockResolvedValue({ success: true, data: mockSection });

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const section = await result.current.getSection('ui');
      expect(section).toEqual(mockSection);
    });

    expect(mockConfigApi.getSection).toHaveBeenCalledWith('ui');
  });

  test('gets change history', async () => {
    const mockHistory = [
      {
        timestamp: Date.now(),
        section: 'ui',
        field: 'theme',
        old_value: 'light',
        new_value: 'dark',
      },
    ];
    mockConfigApi.getChangeHistory.mockResolvedValue({ success: true, data: mockHistory });

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const history = await result.current.getChangeHistory();
      expect(history).toEqual(mockHistory);
    });

    expect(mockConfigApi.getChangeHistory).toHaveBeenCalled();
  });

  test('rolls back config', async () => {
    const mockResponse = { success: true, data: { message: 'Config rolled back' } };
    mockConfigApi.rollbackConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.rollbackConfig(1234567890);
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.rollbackConfig).toHaveBeenCalledWith(1234567890);
  });

  test('exports config', async () => {
    const mockResponse = { success: true, data: { exported_data: 'config content' } };
    mockConfigApi.exportConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.exportConfig('/path/to/config');
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.exportConfig).toHaveBeenCalledWith('/path/to/config');
  });

  test('imports config', async () => {
    const mockResponse = { success: true, data: { message: 'Config imported' } };
    mockConfigApi.importConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.importConfig('/path/to/config');
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.importConfig).toHaveBeenCalledWith('/path/to/config');
  });

  test('reloads config', async () => {
    const mockResponse = { success: true, data: { message: 'Config reloaded' } };
    mockConfigApi.reloadConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.reloadConfig();
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.reloadConfig).toHaveBeenCalled();
  });

  test('resets config', async () => {
    const mockResponse = { success: true, data: { message: 'Config reset' } };
    mockConfigApi.resetConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.resetConfig();
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.resetConfig).toHaveBeenCalled();
  });

  test('validates config', async () => {
    const mockResponse = { success: true, data: { valid: true } };
    mockConfigApi.validateConfig.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useConfig());

    await act(async () => {
      const response = await result.current.validateConfig();
      expect(response).toEqual(mockResponse);
    });

    expect(mockConfigApi.validateConfig).toHaveBeenCalled();
  });

  test('sets local config', () => {
    const { result } = renderHook(() => useConfig());

    act(() => {
      result.current.setLocalConfig('ui', 'theme', 'dark');
    });

    // Should not throw error
  });

  test('gets local config value', () => {
    const { result } = renderHook(() => useConfig());

    const value = result.current.getLocalConfig('ui', 'theme');
    expect(value).toBeDefined();
  });

  test('clears config error', () => {
    const { result } = renderHook(() => useConfig());

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });
});
