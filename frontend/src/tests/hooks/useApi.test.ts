import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useApi,
  useAutoFetch,
  useForm,
  useLocalStorage,
  usePagination,
  useSearch,
  useFileUpload,
} from '@/hooks/useApi';

// Mock notistack
vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

// Mock utils
vi.mock('@/utils', () => ({
  getErrorMessage: (error: unknown) => (error instanceof Error ? error.message : 'Unknown error'),
}));

describe('useApi', () => {
  test('returns initial state', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBeUndefined();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.execute).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  test('executes API function successfully', async () => {
    const mockData = { success: true, data: 'test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute();
      expect(response).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('handles API errors', async () => {
    const mockError = new Error('API Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      await expect(result.current.execute()).rejects.toThrow('API Error');
    });

    expect(result.current.data).toBeUndefined();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('API Error');
  });

  test('resets state', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApi(mockApiFunction, { initial: 'data' }));

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toEqual({ initial: 'data' });
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

describe('useAutoFetch', () => {
  test('auto-fetches data on mount', async () => {
    const mockData = { success: true, data: 'test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useAutoFetch(mockApiFunction));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
      expect(result.current.loading).toBe(false);
    });
  });

  test('provides refetch function', async () => {
    const mockData = { success: true, data: 'test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useAutoFetch(mockApiFunction));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    mockApiFunction.mockClear();

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFunction).toHaveBeenCalledTimes(1);
  });
});

describe('useForm', () => {
  const initialValues = { name: '', email: '' };
  const onSubmitMock = vi.fn();

  beforeEach(() => {
    onSubmitMock.mockClear();
  });

  test('returns initial form state', () => {
    const { result } = renderHook(() => useForm(initialValues, onSubmitMock));

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.isSubmitting).toBe(false);
  });

  test('handles field changes', () => {
    const { result } = renderHook(() => useForm(initialValues, onSubmitMock));

    act(() => {
      result.current.handleChange('name', 'John Doe');
    });

    expect(result.current.values.name).toBe('John Doe');
  });

  test('handles form submission', async () => {
    onSubmitMock.mockResolvedValue(undefined);
    const { result } = renderHook(() => useForm(initialValues, onSubmitMock));

    act(() => {
      result.current.handleChange('name', 'John Doe');
      result.current.handleChange('email', 'john@example.com');
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmitMock).toHaveBeenCalledWith({
      name: 'John Doe',
      email: 'john@example.com',
    });
    expect(result.current.isSubmitting).toBe(false);
  });

  test('resets form', () => {
    const { result } = renderHook(() => useForm(initialValues, onSubmitMock));

    act(() => {
      result.current.handleChange('name', 'John Doe');
      result.current.resetForm();
    });

    expect(result.current.values).toEqual(initialValues);
  });
});

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('returns initial value when no stored value', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default-value'));

    expect(result.current[0]).toBe('default-value');
  });

  test('returns stored value when available', () => {
    localStorage.setItem('test-key', JSON.stringify('stored-value'));
    const { result } = renderHook(() => useLocalStorage('test-key', 'default-value'));

    expect(result.current[0]).toBe('stored-value');
  });

  test('updates stored value', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default-value'));

    act(() => {
      result.current[1]('new-value');
    });

    expect(result.current[0]).toBe('new-value');
    expect(localStorage.getItem('test-key')).toBe(JSON.stringify('new-value'));
  });

  test('handles function-based updates', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 0));

    act(() => {
      result.current[1](prev => prev + 1);
    });

    expect(result.current[0]).toBe(1);
  });
});

describe('usePagination', () => {
  test('returns initial pagination state', () => {
    const { result } = renderHook(() => usePagination());

    expect(result.current.page).toBe(0);
    expect(result.current.rowsPerPage).toBe(10);
  });

  test('handles page changes', () => {
    const { result } = renderHook(() => usePagination());

    act(() => {
      result.current.handleChangePage({}, 5);
    });

    expect(result.current.page).toBe(5);
  });

  test('handles rows per page changes', () => {
    const { result } = renderHook(() => usePagination());

    act(() => {
      const event = { target: { value: '25' } } as React.ChangeEvent<HTMLInputElement>;
      result.current.handleChangeRowsPerPage(event);
    });

    expect(result.current.rowsPerPage).toBe(25);
    expect(result.current.page).toBe(0);
  });

  test('resets pagination', () => {
    const { result } = renderHook(() => usePagination(5, 20));

    act(() => {
      result.current.handleChangePage({}, 10);
      result.current.handleChangeRowsPerPage({
        target: { value: '50' },
      } as React.ChangeEvent<HTMLInputElement>);
      result.current.resetPagination();
    });

    expect(result.current.page).toBe(5);
    expect(result.current.rowsPerPage).toBe(20);
  });
});

describe('useSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('returns initial search state', () => {
    const { result } = renderHook(() => useSearch());

    expect(result.current.query).toBe('');
    expect(result.current.debouncedQuery).toBe('');
  });

  test('updates query immediately', () => {
    const { result } = renderHook(() => useSearch());

    act(() => {
      result.current.setQuery('test');
    });

    expect(result.current.query).toBe('test');
  });

  test('debounces debounced query', () => {
    const { result } = renderHook(() => useSearch('', 300));

    act(() => {
      result.current.setQuery('test');
    });

    expect(result.current.debouncedQuery).toBe('');

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current.debouncedQuery).toBe('test');
  });

  test('resets search', () => {
    const { result } = renderHook(() => useSearch('initial', 300));

    act(() => {
      result.current.setQuery('modified');
      result.current.resetSearch();
    });

    expect(result.current.query).toBe('initial');
  });
});

describe('useFileUpload', () => {
  test('returns initial upload state', () => {
    const mockUploadFunction = vi.fn();
    const { result } = renderHook(() => useFileUpload(mockUploadFunction));

    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.uploadError).toBeNull();
  });

  test('handles successful file upload', async () => {
    const mockData = { success: true };
    const mockUploadFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useFileUpload(mockUploadFunction));

    const files = [new File(['content'], 'test.txt')];

    await act(async () => {
      const response = await result.current.uploadFiles(files);
      expect(response).toEqual(mockData);
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadProgress).toBe(100);
    expect(result.current.uploadError).toBeNull();
  });

  test('handles upload errors', async () => {
    const mockError = new Error('Upload failed');
    const mockUploadFunction = vi.fn().mockRejectedValue(mockError);
    const { result } = renderHook(() => useFileUpload(mockUploadFunction));

    const files = [new File(['content'], 'test.txt')];

    await act(async () => {
      await expect(result.current.uploadFiles(files)).rejects.toThrow('Upload failed');
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadError).toBe('Upload failed');
  });

  test('resets upload state', () => {
    const mockUploadFunction = vi.fn();
    const { result } = renderHook(() => useFileUpload(mockUploadFunction));

    act(() => {
      result.current.resetUpload();
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.uploadError).toBeNull();
  });
});
