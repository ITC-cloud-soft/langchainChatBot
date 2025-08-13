import React, { useState, useEffect, useCallback } from 'react';
import { useSnackbar } from 'notistack';

import { getErrorMessage } from '../utils';

/**
 * API通信の状態を管理するカスタムフック
 * @param apiFunction API関数
 * @param initialData 初期データ
 * @returns API通信の状態と関数
 */
export function useApi<T, P = unknown>(apiFunction: (params?: P) => Promise<T>, initialData?: T) {
  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { enqueueSnackbar } = useSnackbar();

  const execute = useCallback(
    async (params?: P): Promise<T | undefined> => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiFunction(params);
        setData(result);
        return result;
      } catch (err: unknown) {
        const errorMessage = getErrorMessage(err);
        setError(errorMessage);
        enqueueSnackbar(errorMessage, { variant: 'error' });
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, enqueueSnackbar],
  );

  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setLoading(false);
  }, [initialData]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

/**
 * 自動的にデータを取得するカスタムフック
 * @param apiFunction API関数
 * @param params API関数のパラメータ
 * @param initialData 初期データ
 * @param deps 依存配列
 * @returns API通信の状態
 */
export function useAutoFetch<T, P = unknown>(
  apiFunction: (params?: P) => Promise<T>,
  params?: P,
  initialData?: T,
  deps: unknown[] = [],
) {
  const { data, loading, error, execute, reset } = useApi<T, P>(apiFunction, initialData);

  useEffect(() => {
    execute(params);
  }, deps);

  return {
    data,
    loading,
    error,
    refetch: () => execute(params),
    reset,
  };
}

/**
 * フォームの状態を管理するカスタムフック
 * @param initialValues 初期値
 * @param onSubmit 送信時のコールバック
 * @returns フォームの状態と関数
 */
export function useForm<T extends Record<string, unknown>>(
  initialValues: T,
  onSubmit: (values: T) => Promise<void> | void,
) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const handleChange = (field: keyof T, value: unknown) => {
    setValues(prev => ({ ...prev, [field]: value }));
    // フィールドが変更されたらエラーをクリア
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const setFieldValue = (field: keyof T, value: unknown) => {
    setValues(prev => ({ ...prev, [field]: value }));
  };

  const setFieldError = (field: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [field]: error }));
  };

  const resetForm = () => {
    setValues(initialValues);
    setErrors({});
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }

    setIsSubmitting(true);

    try {
      await onSubmit(values);
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error);
      enqueueSnackbar(errorMessage, { variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    values,
    errors,
    isSubmitting,
    handleChange,
    setFieldValue,
    setFieldError,
    resetForm,
    handleSubmit,
  };
}

/**
 * ローカルストレージの状態を管理するカスタムフック
 * @param key ストレージキー
 * @param initialValue 初期値
 * @returns ストレージの値と設定関数
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
}

/**
 * ページネーションの状態を管理するカスタムフック
 * @param initialPage 初期ページ
 * @param initialRowsPerPage 初期行数
 * @returns ページネーションの状態と関数
 */
export function usePagination(initialPage = 0, initialRowsPerPage = 10) {
  const [page, setPage] = useState(initialPage);
  const [rowsPerPage, setRowsPerPage] = useState(initialRowsPerPage);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const resetPagination = () => {
    setPage(initialPage);
    setRowsPerPage(initialRowsPerPage);
  };

  return {
    page,
    rowsPerPage,
    handleChangePage,
    handleChangeRowsPerPage,
    resetPagination,
  };
}

/**
 * 検索クエリの状態を管理するカスタムフック
 * @param initialQuery 初期クエリ
 * @param debounceTime デバウンス時間（ミリ秒）
 * @returns 検索クエリの状態と関数
 */
export function useSearch(initialQuery = '', debounceTime = 300) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceTime);

    return () => {
      clearTimeout(timer);
    };
  }, [query, debounceTime]);

  const resetSearch = () => {
    setQuery(initialQuery);
  };

  return {
    query,
    debouncedQuery,
    setQuery,
    resetSearch,
  };
}

/**
 * ファイルアップロードの状態を管理するカスタムフック
 * @param uploadFunction アップロード関数
 * @returns ファイルアップロードの状態と関数
 */
export function useFileUpload<T = unknown>(uploadFunction: (files: File[]) => Promise<T>) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { enqueueSnackbar } = useSnackbar();

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      const result = await uploadFunction(files);
      setUploadProgress(100);
      enqueueSnackbar('ファイルのアップロードが完了しました', { variant: 'success' });
      return result;
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error);
      setUploadError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setIsUploading(false);
    setUploadProgress(0);
    setUploadError(null);
  };

  return {
    isUploading,
    uploadProgress,
    uploadError,
    uploadFiles,
    resetUpload,
  };
}
