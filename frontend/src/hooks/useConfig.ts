import { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';

import { configApi } from '../services/api';

import { useLocalStorage } from './useApi';

/**
 * アプリケーション設定を管理するカスタムフック
 */
export function useConfig() {
  const { enqueueSnackbar } = useSnackbar();
  const [config, setConfig] = useLocalStorage('app_config', {} as Record<string, unknown>);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 設定を取得する
   */
  const fetchConfig = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.getConfig();
      setConfig(response);
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定の取得に失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定を更新する
   */
  const updateConfig = async (section: string, field: string, value: unknown) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.updateConfig(section, field, value);

      // ローカルの設定を更新
      setConfig(prevConfig => ({
        ...prevConfig,
        [section]: {
          ...((prevConfig as Record<string, Record<string, unknown>>)[section] || {}),
          [field]: value,
        },
      }));

      enqueueSnackbar('設定を更新しました', { variant: 'success' });
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定の更新に失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定セクションを取得する
   */
  const getSection = (section: string) => {
    return (config as Record<string, Record<string, unknown>>)[section] || {};
  };

  /**
   * 設定値を取得する
   */
  const getValue = (section: string, field: string, defaultValue?: unknown) => {
    const sectionConfig = getSection(section);
    return sectionConfig[field] !== undefined ? sectionConfig[field] : defaultValue;
  };

  /**
   * 設定値を設定する（ローカルのみ）
   */
  const setValue = (section: string, field: string, value: unknown) => {
    setConfig(prevConfig => ({
      ...prevConfig,
      [section]: {
        ...((prevConfig as Record<string, Record<string, unknown>>)[section] || {}),
        [field]: value,
      },
    }));
  };

  /**
   * 設定をリセットする
   */
  const resetConfig = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.resetConfig();
      setConfig(response.config || {});
      enqueueSnackbar('設定をリセットしました', { variant: 'success' });
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定のリセットに失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定を再読み込みする
   */
  const reloadConfig = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.reloadConfig();
      setConfig(response.config || {});
      enqueueSnackbar('設定を再読み込みしました', { variant: 'success' });
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定の再読み込みに失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定をエクスポートする
   */
  const exportConfig = async (exportPath: string, format = 'toml') => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.exportConfig(exportPath, format);
      enqueueSnackbar('設定をエクスポートしました', { variant: 'success' });
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定のエクスポートに失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定をインポートする
   */
  const importConfig = async (importPath: string, format = 'toml') => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.importConfig(importPath, format);
      setConfig(response.config || {});
      enqueueSnackbar('設定をインポートしました', { variant: 'success' });
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定のインポートに失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 設定を検証する
   */
  const validateConfig = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await configApi.validateConfig();
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '設定の検証に失敗しました';
      setError(errorMessage);
      enqueueSnackbar(errorMessage, { variant: 'error' });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    config,
    isLoading,
    error,
    fetchConfig,
    updateConfig,
    getSection,
    getValue,
    setValue,
    resetConfig,
    reloadConfig,
    exportConfig,
    importConfig,
    validateConfig,
  };
}

/**
 * テーマ設定を管理するカスタムフック
 */
export function useTheme() {
  const { getValue, setValue } = useConfig();

  const themeMode = getValue('ui', 'theme_mode', 'light');
  const primaryColor = getValue('ui', 'primary_color', '#1976d2');
  const secondaryColor = getValue('ui', 'secondary_color', '#dc004e');

  const setThemeMode = (mode: 'light' | 'dark') => {
    setValue('ui', 'theme_mode', mode);
  };

  const setPrimaryColor = (color: string) => {
    setValue('ui', 'primary_color', color);
  };

  const setSecondaryColor = (color: string) => {
    setValue('ui', 'secondary_color', color);
  };

  return {
    themeMode,
    primaryColor,
    secondaryColor,
    setThemeMode,
    setPrimaryColor,
    setSecondaryColor,
  };
}

/**
 * 言語設定を管理するカスタムフック
 */
export function useLanguage() {
  const { getValue, setValue } = useConfig();

  const language = getValue('ui', 'language', 'ja');

  const setLanguage = (lang: string) => {
    setValue('ui', 'language', lang);
  };

  return {
    language,
    setLanguage,
  };
}

/**
 * ユーザー設定を管理するカスタムフック
 */
export function useUserSettings() {
  const { getValue, setValue } = useConfig();

  const username = getValue('user', 'username', '');
  const email = getValue('user', 'email', '');
  const notifications = getValue('user', 'notifications', true);

  const setUsername = (name: string) => {
    setValue('user', 'username', name);
  };

  const setEmail = (email: string) => {
    setValue('user', 'email', email);
  };

  const setNotifications = (enabled: boolean) => {
    setValue('user', 'notifications', enabled);
  };

  return {
    username,
    email,
    notifications,
    setUsername,
    setEmail,
    setNotifications,
  };
}
