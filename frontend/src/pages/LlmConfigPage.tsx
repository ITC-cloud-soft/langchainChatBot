import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Divider,
  Alert,
  IconButton,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import { llmConfigApi, embeddingConfigApi } from '../services/api';
import { logger } from '../utils/logger';

interface LLMConfig {
  provider: string;
  api_base: string;
  api_key: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
}

interface EmbeddingConfig {
  provider: string;
  base_url: string;
  model_name: string;
  api_key: string;
  dimension: number;
}

interface ConfigResponse {
  config: LLMConfig;
  available_models?: string[];
}

interface EmbeddingConfigResponse {
  config: EmbeddingConfig;
  available_models?: string[];
}

interface TestResponse {
  status: 'success' | 'error' | 'warning';
  message: string;
  vector_db_recreated?: boolean;
  old_dimension?: number;
  new_dimension?: number;
}

type TabValue = 'llm' | 'embedding';

const LlmConfigPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabValue>('llm');
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [embeddingConfig, setEmbeddingConfig] = useState<EmbeddingConfig | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [availableEmbeddingModels, setAvailableEmbeddingModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'success' | 'error' | 'warning'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [dimensionDialogOpen, setDimensionDialogOpen] = useState(false);
  const [isDimensionEditable, setIsDimensionEditable] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  // 現在の埋め込み設定を保存（次元数変更検出用）
  const [originalEmbeddingConfig, setOriginalEmbeddingConfig] = useState<EmbeddingConfig | null>(null);
  
  // 次元数変更確認ポップアップ
  const [dimensionChangeConfirmOpen, setDimensionChangeConfirmOpen] = useState(false);

  const loadConfig = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = (await llmConfigApi.getConfig()) as ConfigResponse;
      setConfig(response.config);
      // Also set available models from the config response
      if (response.available_models && Array.isArray(response.available_models)) {
        setAvailableModels(response.available_models);
      }
    } catch (error) {
      logger.error('Error loading config:', error);
      const errorMessage = (error as Error).message || '設定の読み込み中にエラーが発生しました';
      enqueueSnackbar(errorMessage, { variant: 'error' });
      // エラー時にデフォルト設定をセット
      setConfig({
        provider: 'openai',
        api_base: 'https://api.openai.com/v1',
        api_key: 'nokey',
        model_name: 'gpt-3.5-turbo',
        temperature: 0.7,
        max_tokens: 128000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
      });
    } finally {
      setIsLoading(false);
    }
  }, [enqueueSnackbar]);

  const loadAvailableModels = useCallback(async () => {
    try {
      const response = await llmConfigApi.getAvailableModels();
      // Handle different response formats
      if (Array.isArray(response)) {
        setAvailableModels(response);
      } else if (response.data && Array.isArray(response.data)) {
        setAvailableModels(response.data);
      } else if (response.config?.available_models) {
        setAvailableModels(response.config.available_models);
      } else {
        logger.warn('Unexpected response format for models:', response);
        setAvailableModels([]);
      }
    } catch (error) {
      logger.error('Error loading available models:', error);
      enqueueSnackbar('利用可能なモデルの読み込み中にエラーが発生しました', { variant: 'error' });
    }
  }, [enqueueSnackbar]);

  const loadEmbeddingConfig = useCallback(async () => {
    try {
      console.log('Loading embedding config...');
      const response = (await embeddingConfigApi.getConfig()) as EmbeddingConfigResponse;
      console.log('Embedding config response:', response);
      
      // 元の設定を保存（次元数変更検出用）
      setOriginalEmbeddingConfig(response.config);
      setEmbeddingConfig(response.config);
      
      // Also set available models from the config response
      if (response.available_models && Array.isArray(response.available_models)) {
        console.log('Setting available embedding models from config response:', response.available_models);
        setAvailableEmbeddingModels(response.available_models);
      } else {
        console.log('No available_models found in config response, will load separately');
      }
    } catch (error) {
      logger.error('Error loading embedding config:', error);
      console.error('Detailed embedding config error:', error);
      const errorMessage =
        (error as Error).message || '埋め込み設定の読み込み中にエラーが発生しました';
      enqueueSnackbar(errorMessage, { variant: 'error' });
      // エラー時にデフォルト設定をセット
      const defaultConfig = {
        provider: 'ollama',
        base_url: 'http://localhost:11434',
        model_name: 'nomic-embed-text:latest',
        api_key: '',
        dimension: 768,
      };
      setOriginalEmbeddingConfig(defaultConfig);
      setEmbeddingConfig(defaultConfig);
    }
  }, [enqueueSnackbar]);

  const loadAvailableEmbeddingModels = useCallback(async () => {
    try {
      const response = await embeddingConfigApi.getAvailableModels();
      console.log('Raw embedding models API response:', response);
      console.log('Response type:', typeof response);
      console.log('Is array:', Array.isArray(response));
      
      // Handle different response formats
      let models: string[] = [];
      if (Array.isArray(response)) {
        models = response;
        console.log('Using direct array response');
      } else if (response && typeof response === 'object') {
        if (response.data && Array.isArray(response.data)) {
          models = response.data;
          console.log('Using response.data array');
        } else if (response.config?.available_models && Array.isArray(response.config.available_models)) {
          models = response.config.available_models;
          console.log('Using response.config.available_models array');
        } else {
          console.warn('Response object found but no recognizable model array:', response);
          models = [];
        }
      } else {
        console.warn('Unexpected response format for embedding models:', response);
        models = [];
      }
      
      console.log('Final extracted models:', models);
      console.log('Models count:', models.length);
      
      setAvailableEmbeddingModels(models);
      
      if (models.length > 0) {
        console.log('Successfully loaded', models.length, 'embedding models');
      } else {
        console.warn('No embedding models were loaded');
      }
    } catch (error) {
      logger.error('Error loading available embedding models:', error);
      console.error('Detailed error:', error);
      enqueueSnackbar('利用可能な埋め込みモデルの読み込み中にエラーが発生しました', {
        variant: 'error',
      });
      setAvailableEmbeddingModels([]);
    }
  }, [enqueueSnackbar]);

  // Load config on component mount
  useEffect(() => {
    loadConfig();
    loadAvailableModels();
    loadEmbeddingConfig();
    loadAvailableEmbeddingModels();
  }, []); // Empty dependency array to run only on mount

  // Debug: Monitor availableEmbeddingModels changes (可以在生産環境中移除)
  // useEffect(() => {
  //   console.log('availableEmbeddingModels state changed:', availableEmbeddingModels);
  //   console.log('availableEmbeddingModels length:', availableEmbeddingModels?.length);
  // }, [availableEmbeddingModels]);

  const handleRefreshModels = async () => {
    if (!config) return;
    try {
      const response = await llmConfigApi.getModelsFromApi(
        config as unknown as Record<string, unknown>,
      );
      // Handle different response formats
      if (Array.isArray(response)) {
        setAvailableModels(response);
      } else if (response.data && Array.isArray(response.data)) {
        setAvailableModels(response.data);
      } else {
        setAvailableModels([]);
      }
      
      if (response && response.length > 0) {
        enqueueSnackbar('モデルリストを更新しました', { variant: 'success' });
      } else {
        enqueueSnackbar('利用可能なモデルが見つかりませんでした', { variant: 'warning' });
      }
    } catch (error) {
      logger.error('Error refreshing models:', error);
      enqueueSnackbar('モデルリストの更新中にエラーが発生しました', { variant: 'error' });
    }
  };

  // 共通のモデル取得関数
  const fetchModelsFromConfig = async (testConfig: any, sourceDescription: string) => {
    try {
      const response = await llmConfigApi.getModelsFromApi(testConfig);
      // Handle different response formats
      if (Array.isArray(response)) {
        setAvailableModels(response);
      } else if (response.data && Array.isArray(response.data)) {
        setAvailableModels(response.data);
      } else {
        setAvailableModels([]);
      }
      
      if (response && response.length > 0) {
        enqueueSnackbar(`${sourceDescription}によりモデルリストを取得しました`, { variant: 'success' });
      } else {
        enqueueSnackbar('利用可能なモデルが見つかりませんでした', { variant: 'warning' });
      }
    } catch (error) {
      logger.error(`Error getting models from ${sourceDescription}:`, error);
      // Don't show error for automatic model fetching
    }
  };

  const handleApiBaseChange = async (apiBase: string) => {
    if (!config) return;
    // Update config
    handleInputChange('api_base', apiBase);

    // Try to get models from the new API base
    if (apiBase && apiBase.trim() !== '') {
      const testConfig = {
        ...config,
        api_base: apiBase,
      };
      await fetchModelsFromConfig(testConfig, 'APIベースURL');
    }
  };

  const handleApiKeyChange = async (apiKey: string) => {
    if (!config) return;
    // Update config
    handleInputChange('api_key', apiKey);

    // Try to get models from the new API key
    if (apiKey && apiKey !== 'nokey') {
      const testConfig = {
        ...config,
        api_key: apiKey,
      };
      await fetchModelsFromConfig(testConfig, 'APIキー');
    }
  };

  const handleProviderChange = async (provider: string) => {
    if (!config) return;
    // Update config
    handleInputChange('provider', provider);

    // Only set defaults if the current values are empty or invalid
    let needsApiBaseUpdate = !config.api_base || config.api_base.trim() === '';
    let needsModelUpdate = !config.model_name || config.model_name.trim() === '';

    let newApiBase = config.api_base;
    let newModelName = config.model_name;

    if (needsApiBaseUpdate) {
      switch (provider) {
        case 'openai':
          newApiBase = 'https://api.openai.com/v1';
          break;
        case 'anthropic':
          newApiBase = 'https://api.anthropic.com';
          break;
        case 'gemini':
          newApiBase = 'https://generativelanguage.googleapis.com/v1';
          break;
        case 'カスタム':
          newApiBase = 'http://localhost:11434/v1';
          break;
        default:
          newApiBase = 'http://localhost:11434/v1';
      }
    }

    if (needsModelUpdate) {
      switch (provider) {
        case 'openai':
          newModelName = 'gpt-3.5-turbo';
          break;
        case 'anthropic':
          newModelName = 'claude-3-sonnet-20240229';
          break;
        case 'gemini':
          newModelName = 'gemini-pro';
          break;
        case 'カスタム':
          newModelName = '';
          break;
        default:
          newModelName = '';
      }
    }

    // Update API base and model name only if needed
    if (needsApiBaseUpdate) {
      handleInputChange('api_base', newApiBase);
    }
    if (needsModelUpdate) {
      handleInputChange('model_name', newModelName);
    }

    // Try to get models for the new provider
    if (provider === 'カスタム' && newApiBase) {
      try {
        const testConfig = {
          ...config,
          provider: provider,
          api_base: newApiBase,
        };
        const response = await llmConfigApi.getModelsFromApi(testConfig);
        // Handle different response formats
        if (Array.isArray(response)) {
          setAvailableModels(response);
        } else if (response.data && Array.isArray(response.data)) {
          setAvailableModels(response.data);
        } else {
          setAvailableModels([]);
        }
        enqueueSnackbar(`${provider}のモデルリストを取得しました`, { variant: 'success' });
      } catch (error) {
        logger.error('Error getting models for new provider:', error);
        // Don't show error for automatic model fetching
      }
    } else {
      // For non-カスタム providers, set the current model in available models
      if (newModelName) {
        setAvailableModels([newModelName]);
      }
    }
  };

  const handleSaveConfig = async () => {
    if (!config) return;
    setIsLoading(true);
    try {
      await llmConfigApi.updateConfig(config as unknown as Record<string, unknown>);
      enqueueSnackbar('設定を保存しました', { variant: 'success' });
    } catch (error) {
      logger.error('Error saving config:', error);
      enqueueSnackbar('設定の保存中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConfig = async () => {
    if (!config) return;
    setIsTesting(true);
    setTestStatus('idle');
    setTestMessage('');

    try {
      const response = (await llmConfigApi.testConfig(
        config as unknown as Record<string, unknown>,
      )) as TestResponse;
      setTestStatus(response.status === 'success' ? 'success' : 'error');
      setTestMessage(response.message);

      if (response.status === 'success') {
        enqueueSnackbar('設定テストに成功しました', { variant: 'success' });
      } else {
        enqueueSnackbar('設定テストに失敗しました', { variant: 'error' });
      }
    } catch (error) {
      logger.error('Error testing config:', error);
      setTestStatus('error');
      setTestMessage('テスト中にエラーが発生しました');
      enqueueSnackbar('設定テスト中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleResetConfig = async () => {
    setIsLoading(true);
    try {
      const response = (await llmConfigApi.getDefaultConfig()) as LLMConfig;
      setConfig(response);
      enqueueSnackbar('設定をデフォルトにリセットしました', { variant: 'success' });
    } catch (error) {
      logger.error('Error resetting config:', error);
      enqueueSnackbar('設定のリセット中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportConfig = async () => {
    try {
      const configData = await llmConfigApi.exportConfig();
      const blob = new Blob([JSON.stringify(configData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'llm-config.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      enqueueSnackbar('設定をエクスポートしました', { variant: 'success' });
    } catch (error) {
      logger.error('Error exporting config:', error);
      enqueueSnackbar('設定のエクスポート中にエラーが発生しました', { variant: 'error' });
    }
  };

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async e => {
      try {
        const content = e.target?.result;
        if (!content || typeof content !== 'string') {
          throw new Error('ファイルの読み取りに失敗しました');
        }
        const importedConfig = JSON.parse(content);

        setIsLoading(true);
        const response = (await llmConfigApi.importConfig(file)) as ConfigResponse;
        setConfig(response.config || importedConfig);
        enqueueSnackbar('設定をインポートしました', { variant: 'success' });
      } catch (error) {
        logger.error('Error importing config:', error);
        enqueueSnackbar('設定のインポート中にエラーが発生しました', { variant: 'error' });
      } finally {
        setIsLoading(false);
        // Reset file input
        event.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: TabValue) => {
    setActiveTab(newValue);
  };

  const handleEmbeddingProviderChange = async (provider: string) => {
    if (!embeddingConfig) return;
    // Update config
    handleEmbeddingInputChange('provider', provider);

    // プロバイダー変更時は常にデフォルト設定を適用
    let needsApiBaseUpdate = true; // プロバイダー変更時は常にAPI URLを更新
    let needsModelUpdate = true; // プロバイダー変更時は常にモデル名を更新
    let needsDimensionUpdate = !embeddingConfig.dimension || embeddingConfig.dimension === 0;

    let newApiBase = embeddingConfig.base_url;
    let newModelName = embeddingConfig.model_name;
    let newDimension = embeddingConfig.dimension;

    if (needsApiBaseUpdate) {
      switch (provider) {
        case 'ollama':
          newApiBase = 'http://localhost:11434';
          break;
        case 'openai':
          newApiBase = 'https://api.openai.com/v1';
          break;
        case 'カスタム':
          newApiBase = 'http://localhost:11434/v1';
          break;
        default:
          newApiBase = 'http://localhost:11434';
      }
    }

    if (needsModelUpdate) {
      switch (provider) {
        case 'ollama':
          newModelName = 'nomic-embed-text:latest';
          break;
        case 'openai':
          newModelName = 'text-embedding-3-small';
          break;
        case 'カスタム':
          newModelName = 'custom-embedding-model';
          break;
        default:
          newModelName = 'nomic-embed-text:latest';
      }
    }

    if (needsDimensionUpdate) {
      switch (provider) {
        case 'ollama':
          newDimension = 768;
          break;
        case 'openai':
          newDimension = 1536;
          break;
        case 'カスタム':
          newDimension = 768;
          break;
        default:
          newDimension = 768;
      }
    }

    // Update API base, model name, and dimension according to provider change
    if (needsApiBaseUpdate) {
      console.log(`Updating API base for provider ${provider}: ${newApiBase}`);
      handleEmbeddingInputChange('base_url', newApiBase);
    }
    if (needsModelUpdate) {
      console.log(`Updating model name for provider ${provider}: ${newModelName}`);
      handleEmbeddingInputChange('model_name', newModelName);
    }
    if (needsDimensionUpdate) {
      console.log(`Updating dimension for provider ${provider}: ${newDimension}`);
      handleEmbeddingInputChange('dimension', newDimension);
    }

    // すべてのプロバイダーでモデルを取得しようと試みる
    if (newApiBase) {
      await fetchEmbeddingModelsFromProvider(provider, newApiBase, embeddingConfig.api_key);
    }
  };

  // プロバイダー指定でのモデル取得関数
  const fetchEmbeddingModelsFromProvider = async (provider: string, baseUrl: string, apiKey: string = '') => {
    try {
      console.log(`Fetching embedding models from provider: ${provider}, baseUrl: ${baseUrl}`);
      const response = await embeddingConfigApi.getModelsForProvider({
        provider: provider,
        base_url: baseUrl,
        api_key: apiKey
      });
      console.log('fetchEmbeddingModelsFromProvider response:', response);
      console.log('Response type:', typeof response);
      console.log('Is array:', Array.isArray(response));
      
      // Handle different response formats
      let models: string[] = [];
      if (Array.isArray(response)) {
        models = response;
        console.log('Using direct array response from provider', provider);
      } else if (response && typeof response === 'object') {
        if (response.data && Array.isArray(response.data)) {
          models = response.data;
          console.log('Using response.data array from provider', provider);
        } else {
          console.warn('Response object found but no recognizable model array from provider', provider, ':', response);
          models = [];
        }
      } else {
        console.warn('Unexpected response format from provider', provider, ':', response);
        models = [];
      }
      
      console.log('Final extracted models from provider', provider, ':', models);
      console.log('Models count from provider', provider, ':', models.length);
      
      setAvailableEmbeddingModels(models);
      
      // Auto-select first model only if no model is currently set
      if (models.length > 0 && embeddingConfig && (!embeddingConfig.model_name || embeddingConfig.model_name.trim() === '')) {
        console.log(`Auto-selecting first model: ${models[0]} (no current model set)`);
        handleEmbeddingInputChange('model_name', models[0]);
      }
      
      if (models && models.length > 0) {
        enqueueSnackbar(`${provider}プロバイダーにより埋め込みモデルリストを取得しました (${models.length}件)`, { variant: 'success' });
      } else {
        enqueueSnackbar(`${provider}プロバイダーで利用可能な埋め込みモデルが見つかりませんでした`, { variant: 'warning' });
      }
    } catch (error) {
      console.error(`Error getting embedding models from provider ${provider}:`, error);
      logger.error(`Error getting embedding models from provider ${provider}:`, error);
      // Don't show error for automatic model fetching
      setAvailableEmbeddingModels([]);
    }
  };

  // 埋め込みモデル用の共通取得関数
  const fetchEmbeddingModelsFromConfig = async (sourceDescription: string) => {
    try {
      console.log(`Fetching embedding models from ${sourceDescription}...`);
      const response = await embeddingConfigApi.getAvailableModels();
      console.log('fetchEmbeddingModelsFromConfig response:', response);
      console.log('Response type:', typeof response);
      console.log('Is array:', Array.isArray(response));
      
      // Handle different response formats
      let models: string[] = [];
      if (Array.isArray(response)) {
        models = response;
        console.log('Using direct array response from', sourceDescription);
      } else if (response && typeof response === 'object') {
        if (response.data && Array.isArray(response.data)) {
          models = response.data;
          console.log('Using response.data array from', sourceDescription);
        } else {
          console.warn('Response object found but no recognizable model array from', sourceDescription, ':', response);
          models = [];
        }
      } else {
        console.warn('Unexpected response format from', sourceDescription, ':', response);
        models = [];
      }
      
      console.log('Final extracted models from', sourceDescription, ':', models);
      console.log('Models count from', sourceDescription, ':', models.length);
      
      setAvailableEmbeddingModels(models);
      
      // Auto-select first model only if no model is currently set
      if (models.length > 0 && embeddingConfig && (!embeddingConfig.model_name || embeddingConfig.model_name.trim() === '')) {
        console.log(`Auto-selecting first model: ${models[0]} (no current model set)`);
        handleEmbeddingInputChange('model_name', models[0]);
      }
      
      if (models && models.length > 0) {
        enqueueSnackbar(`${sourceDescription}により埋め込みモデルリストを取得しました (${models.length}件)`, { variant: 'success' });
      } else {
        enqueueSnackbar('利用可能な埋め込みモデルが見つかりませんでした', { variant: 'warning' });
      }
    } catch (error) {
      console.error(`Error getting embedding models from ${sourceDescription}:`, error);
      logger.error(`Error getting embedding models from ${sourceDescription}:`, error);
      // Don't show error for automatic model fetching
      setAvailableEmbeddingModels([]);
    }
  };

  const handleEmbeddingApiBaseChange = async (apiBase: string) => {
    if (!embeddingConfig) return;
    // Update config
    handleEmbeddingInputChange('base_url', apiBase);

    // Try to get models from the new API base
    if (apiBase && apiBase.trim() !== '') {
      await fetchEmbeddingModelsFromConfig('APIベースURL');
    }
  };

  // 埋め込みAPIキー変更ハンドラーを追加
  const handleEmbeddingApiKeyChange = async (apiKey: string) => {
    if (!embeddingConfig) return;
    // Update config
    handleEmbeddingInputChange('api_key', apiKey);

    // Try to get models from the new API key
    if (apiKey && apiKey.trim() !== '') {
      await fetchEmbeddingModelsFromConfig('APIキー');
    }
  };

  const handleRefreshEmbeddingModels = async () => {
    if (!embeddingConfig) return;
    try {
      console.log('Refreshing embedding models...');
      console.log('Current embedding config:', embeddingConfig);
      
      const response = await embeddingConfigApi.refreshAvailableModels();
      console.log('Refresh embedding models response:', response);
      console.log('Response type:', typeof response);
      console.log('Is array:', Array.isArray(response));
      
      // Handle different response formats
      let models: string[] = [];
      if (Array.isArray(response)) {
        models = response;
        console.log('Using direct array response for refresh');
      } else if (response && typeof response === 'object') {
        if (response.data && Array.isArray(response.data)) {
          models = response.data;
          console.log('Using response.data array for refresh');
        } else {
          console.warn('Response object found but no recognizable model array for refresh:', response);
          models = [];
        }
      } else {
        console.warn('Unexpected response format for refresh:', response);
        models = [];
      }
      
      console.log('Final extracted models for refresh:', models);
      console.log('Models count for refresh:', models.length);
      
      setAvailableEmbeddingModels(models);
      
      // Auto-select first model only if no model is currently set
      if (models.length > 0 && embeddingConfig && (!embeddingConfig.model_name || embeddingConfig.model_name.trim() === '')) {
        console.log(`Auto-selecting first model on refresh: ${models[0]} (no current model set)`);
        handleEmbeddingInputChange('model_name', models[0]);
      }
      
      if (models.length > 0) {
        enqueueSnackbar(`埋め込みモデルリストを更新しました (${models.length}件)`, { variant: 'success' });
      } else {
        enqueueSnackbar('利用可能な埋め込みモデルが見つかりませんでした', { variant: 'warning' });
      }
    } catch (error) {
      console.error('Error refreshing embedding models:', error);
      logger.error('Error refreshing embedding models:', error);
      enqueueSnackbar('埋め込みモデルリストの更新中にエラーが発生しました', { variant: 'error' });
      setAvailableEmbeddingModels([]);
    }
  };

  const handleSaveEmbeddingConfig = async () => {
    if (!embeddingConfig || !originalEmbeddingConfig) return;
    
    // 次元数が変更されたかチェック
    const dimensionChanged = originalEmbeddingConfig.dimension !== embeddingConfig.dimension;
    
    if (dimensionChanged) {
      // 次元数が変更された場合は確認ポップアップを表示
      setDimensionChangeConfirmOpen(true);
      return;
    }
    
    // 次元数が変更されていない場合は通常保存
    await performSaveEmbeddingConfig();
  };

  const performSaveEmbeddingConfig = async () => {
    if (!embeddingConfig || !originalEmbeddingConfig) return;
    setIsLoading(true);
    
    // 次元数が変更されたかチェック
    const dimensionChanged = originalEmbeddingConfig.dimension !== embeddingConfig.dimension;
    
    try {
      const response = (await embeddingConfigApi.updateConfig(embeddingConfig as unknown as Record<string, unknown>)) as TestResponse;
      
      // レスポンスを解析して適切なメッセージを表示
      if (response.vector_db_recreated) {
        // ベクトルDBが再作成された場合
        enqueueSnackbar(response.message, { variant: 'success' });
        
        // 再作成の詳細情報を表示
        if (response.old_dimension && response.new_dimension) {
          enqueueSnackbar(
            `ベクトルデータベースを次元数 ${response.old_dimension} から ${response.new_dimension} に再作成しました`, 
            { variant: 'info' }
          );
        }
      } else if (dimensionChanged && response.status === 'warning') {
        // 次元数は変更されたが、ベクトルDB再作成に失敗した場合
        enqueueSnackbar(response.message, { variant: 'warning' });
        
        if (response.old_dimension && response.new_dimension) {
          enqueueSnackbar(
            `手動でベクトルデータベースを再作成してください（次元数: ${response.old_dimension} → ${response.new_dimension}）`, 
            { variant: 'warning' }
          );
        }
      } else if (dimensionChanged) {
        // 次元数が変更されたが、ベクトルDB再作成情報がない場合
        enqueueSnackbar('埋め込み設定を保存しました。ベクトルデータベースの再作成が必要です。', { variant: 'warning' });
      } else {
        // 次元数が変更されていない場合
        enqueueSnackbar('埋め込み設定を保存しました', { variant: 'success' });
      }
      
      // 元の設定を更新
      setOriginalEmbeddingConfig(embeddingConfig);
      
    } catch (error) {
      logger.error('Error saving embedding config:', error);
      enqueueSnackbar('埋め込み設定の保存中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmDimensionChange = () => {
    setDimensionChangeConfirmOpen(false);
    performSaveEmbeddingConfig();
  };

  const handleCancelDimensionChange = () => {
    setDimensionChangeConfirmOpen(false);
    // 元の次元数に戻す
    if (originalEmbeddingConfig && embeddingConfig) {
      setEmbeddingConfig({
        ...embeddingConfig,
        dimension: originalEmbeddingConfig.dimension
      });
      enqueueSnackbar('ベクトル次元数の変更をキャンセルしました', { variant: 'info' });
    }
  };

  const handleTestEmbeddingConfig = async () => {
    if (!embeddingConfig) return;
    setIsTesting(true);
    setTestStatus('idle');
    setTestMessage('');

    try {
      const response = (await embeddingConfigApi.testConfig(
        embeddingConfig as unknown as Record<string, unknown>,
      )) as TestResponse;
      setTestStatus(response.status);
      setTestMessage(response.message);

      if (response.status === 'success') {
        enqueueSnackbar('埋め込み設定テストに成功しました', { variant: 'success' });
        
        // ベクトルDB再作成の情報があれば表示
        if (response.vector_db_recreated) {
          enqueueSnackbar(response.message, { variant: 'info' });
        }
      } else if (response.status === 'warning') {
        enqueueSnackbar(response.message, { variant: 'warning' });
      } else {
        enqueueSnackbar('埋め込み設定テストに失敗しました', { variant: 'error' });
      }
    } catch (error) {
      logger.error('Error testing embedding config:', error);
      setTestStatus('error');
      setTestMessage('テスト中にエラーが発生しました');
      enqueueSnackbar('埋め込み設定テスト中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleResetEmbeddingConfig = async () => {
    setIsLoading(true);
    try {
      const response = (await embeddingConfigApi.getDefaultConfig()) as EmbeddingConfig;
      setEmbeddingConfig(response);
      enqueueSnackbar('埋め込み設定をデフォルトにリセットしました', { variant: 'success' });
    } catch (error) {
      logger.error('Error resetting embedding config:', error);
      enqueueSnackbar('埋め込み設定のリセット中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmbeddingInputChange = (
    field: keyof EmbeddingConfig,
    value: string | number | boolean | number[],
  ) => {
    setEmbeddingConfig(prev => {
      if (!prev) return null;
      return {
        ...prev,
        [field]: value,
      };
    });
  };

  const handleInputChange = (
    field: keyof LLMConfig,
    value: string | number | boolean | number[],
  ) => {
    setConfig(prev => {
      if (!prev) return null;
      return {
        ...prev,
        [field]: value,
      };
    });
  };

  if (isLoading || !config || !embeddingConfig) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Debug: Log current state before rendering (本番環境では削除推奨)
  // console.log('=== LlmConfigPage Render Debug ===');
  // console.log('availableEmbeddingModels:', availableEmbeddingModels);
  // console.log('availableEmbeddingModels length:', availableEmbeddingModels?.length);
  // console.log('embeddingConfig.model_name:', embeddingConfig?.model_name);
  // console.log('embeddingConfig.provider:', embeddingConfig?.provider);
  // console.log('================================');

  return (
    <Box sx={{ height: '100%' }}>
      <Typography variant="h4" gutterBottom>
        LLM設定
      </Typography>

      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="基本LLM設定" value="llm" />
        <Tab label="埋め込みモデル設定" value="embedding" />
      </Tabs>

      {activeTab === 'llm' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                基本設定
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>プロバイダー</InputLabel>
                    <Select
                      value={config.provider}
                      label="プロバイダー"
                      onChange={e => handleProviderChange(e.target.value)}
                    >
                      <MenuItem value="openai">OpenAI</MenuItem>
                      <MenuItem value="anthropic">Anthropic</MenuItem>
                      <MenuItem value="gemini">Gemini</MenuItem>
                      <MenuItem value="カスタム">カスタムAPI</MenuItem>
                    </Select>
                    <Typography variant="caption" color="text.secondary">
                      使用するLLMプロバイダーを選択します
                      {config.provider === 'openai' && (
                        <Typography component="div" variant="caption" color="info.main" sx={{ mt: 0.5 }}>
                          OpenAIは標準API URL (https://api.openai.com/v1) を使用します
                        </Typography>
                      )}
                      {config.provider === 'anthropic' && (
                        <Typography component="div" variant="caption" color="info.main" sx={{ mt: 0.5 }}>
                          Anthropic Claudeの標準API URL (https://api.anthropic.com) を使用します
                        </Typography>
                      )}
                      {config.provider === 'gemini' && (
                        <Typography component="div" variant="caption" color="info.main" sx={{ mt: 0.5 }}>
                          Google Geminiの標準API URL (https://generativelanguage.googleapis.com/v1) を使用します
                        </Typography>
                      )}
                      {config.provider === 'カスタム' && (
                        <Typography component="div" variant="caption" color="warning.main" sx={{ mt: 0.5 }}>
                          カスタムAPIではAPIベースURLを手動で設定する必要があります
                        </Typography>
                      )}
                    </Typography>
                  </FormControl>
                </Grid>

                {config.provider === 'カスタム' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="API Base URL"
                      value={config.api_base}
                      onChange={e => handleApiBaseChange(e.target.value)}
                      placeholder="http://localhost:11434/v1"
                      helperText="LLM APIのベースURL"
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="API Key"
                    value={config.api_key}
                    onChange={e => handleApiKeyChange(e.target.value)}
                    placeholder="nokey"
                    type="password"
                    helperText="LLM APIのキー"
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>モデル名</InputLabel>
                    <Select
                      value={config.model_name}
                      label="モデル名"
                      onChange={e => handleInputChange('model_name', e.target.value)}
                    >
                      {availableModels && availableModels.length > 0 ? (
                        availableModels.map(model => (
                          <MenuItem key={model} value={model}>
                            {model}
                          </MenuItem>
                        ))
                      ) : (
                        <MenuItem value="" disabled>
                          利用可能なモデルがありません
                        </MenuItem>
                      )}
                    </Select>
                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                      <IconButton onClick={handleRefreshModels} size="small">
                        <RefreshIcon />
                      </IconButton>
                      <Typography variant="caption" color="text.secondary">
                        利用可能なモデルを更新
                      </Typography>
                    </Box>
                    {(!availableModels || availableModels.length === 0) && (
                      <Typography variant="caption" color="error" sx={{ mt: 1 }}>
                        APIキーまたはAPIベースURLを確認してください
                      </Typography>
                    )}
                  </FormControl>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              <Typography variant="h6" gutterBottom>
                詳細設定
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography gutterBottom>Temperature: {config.temperature}</Typography>
                  <Slider
                    value={config.temperature}
                    onChange={(_, value) => handleInputChange('temperature', value as number)}
                    min={0}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 0.5, label: '0.5' },
                      { value: 1, label: '1' },
                      { value: 1.5, label: '1.5' },
                      { value: 2, label: '2' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    生成するテキストのランダム性を制御します。値が低いほど決定的な応答になります。
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Max Tokens"
                    type="number"
                    value={config.max_tokens}
                    onChange={e => handleInputChange('max_tokens', parseInt(e.target.value) || 1)}
                    inputProps={{ min: 1 }}
                    helperText="生成するトークンの最大数"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography gutterBottom>Top P: {config.top_p}</Typography>
                  <Slider
                    value={config.top_p}
                    onChange={(_, value) => handleInputChange('top_p', value as number)}
                    min={0}
                    max={1}
                    step={0.05}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 0.5, label: '0.5' },
                      { value: 1, label: '1' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    トークン選択の多様性を制御します。値が低いほど多様性が低くなります。
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Typography gutterBottom>
                    Frequency Penalty: {config.frequency_penalty}
                  </Typography>
                  <Slider
                    value={config.frequency_penalty}
                    onChange={(_, value) => handleInputChange('frequency_penalty', value as number)}
                    min={-2}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: -2, label: '-2' },
                      { value: 0, label: '0' },
                      { value: 2, label: '2' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    既に出現した単語の再出現をペナルティします。
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Typography gutterBottom>Presence Penalty: {config.presence_penalty}</Typography>
                  <Slider
                    value={config.presence_penalty}
                    onChange={(_, value) => handleInputChange('presence_penalty', value as number)}
                    min={-2}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: -2, label: '-2' },
                      { value: 0, label: '0' },
                      { value: 2, label: '2' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    新しいトピックの導入を促進します。
                  </Typography>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={handleSaveConfig}
                  disabled={isLoading}
                >
                  保存
                </Button>

                <Button variant="outlined" onClick={handleResetConfig} disabled={isLoading}>
                  デフォルトにリセット
                </Button>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  設定テスト
                </Typography>

                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={isTesting ? <CircularProgress size={20} /> : <CheckIcon />}
                  onClick={handleTestConfig}
                  disabled={
                    isTesting ||
                    !config?.api_base ||
                    !config?.model_name ||
                    !config?.provider ||
                    config?.model_name.trim() === ''
                  }
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  テスト実行
                </Button>

                {testStatus !== 'idle' && (
                  <Alert
                    severity={testStatus}
                    icon={testStatus === 'success' ? <CheckIcon /> : testStatus === 'error' ? <ErrorIcon /> : undefined}
                    sx={{ mb: 2 }}
                  >
                    {testMessage}
                  </Alert>
                )}

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBottom>
                  設定のインポート/エクスポート
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={handleExportConfig}
                    fullWidth
                  >
                    エクスポート
                  </Button>

                  <Button variant="outlined" component="label" startIcon={<UploadIcon />} fullWidth>
                    インポート
                    <input type="file" accept=".json" hidden onChange={handleImportConfig} />
                  </Button>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBottom>
                  現在の設定
                </Typography>

                <Box sx={{ fontSize: '0.875rem' }}>
                  <Typography variant="body2">
                    <strong>プロバイダー:</strong> {config?.provider}
                  </Typography>
                  <Typography variant="body2">
                    <strong>API Base:</strong> {config?.api_base}
                  </Typography>
                  <Typography variant="body2">
                    <strong>モデル:</strong> {config?.model_name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Temperature:</strong> {config?.temperature}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Max Tokens:</strong> {config?.max_tokens}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 'embedding' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                埋め込みモデル設定
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>プロバイダー</InputLabel>
                    <Select
                      value={embeddingConfig.provider}
                      label="プロバイダー"
                      onChange={e => handleEmbeddingProviderChange(e.target.value)}
                    >
                      <MenuItem value="ollama">Ollama</MenuItem>
                      <MenuItem value="openai">OpenAI</MenuItem>
                      <MenuItem value="カスタム">カスタムAPI</MenuItem>
                    </Select>
                    <Typography variant="caption" color="text.secondary">
                      使用する埋め込みプロバイダーを選択します
                      {embeddingConfig.provider === 'ollama' && (
                        <Typography component="div" variant="caption" color="info.main" sx={{ mt: 0.5 }}>
                          Ollamaは標準API URL (http://localhost:11434) を使用します。APIキーは不要です
                        </Typography>
                      )}
                      {embeddingConfig.provider === 'openai' && (
                        <Typography component="div" variant="caption" color="info.main" sx={{ mt: 0.5 }}>
                          OpenAIは標準API URL (https://api.openai.com/v1) を使用します
                        </Typography>
                      )}
                      {embeddingConfig.provider === 'カスタム' && (
                        <Typography component="div" variant="caption" color="warning.main" sx={{ mt: 0.5 }}>
                          カスタムAPIではAPIベースURLを手動で設定する必要があります
                        </Typography>
                      )}
                    </Typography>
                  </FormControl>
                </Grid>

                {embeddingConfig.provider !== 'openai' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="API Base URL"
                      value={embeddingConfig.base_url}
                      onChange={e => handleEmbeddingApiBaseChange(e.target.value)}
                      placeholder="http://localhost:11434"
                      helperText="埋め込みAPIのベースURL"
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="API Key"
                    value={embeddingConfig.api_key}
                    onChange={e => handleEmbeddingApiKeyChange(e.target.value)}
                    placeholder=""
                    type="password"
                    helperText="埋め込みAPIのキー（Ollamaの場合は不要）"
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>モデル名</InputLabel>
                    <Select
                      value={
                        availableEmbeddingModels && availableEmbeddingModels.length > 0
                          ? embeddingConfig.model_name || ''
                          : ''
                      }
                      label="モデル名"
                      onChange={e => {
                        console.log('Select onChange:', e.target.value);
                        handleEmbeddingInputChange('model_name', e.target.value);
                      }}
                    >
                      {(() => {
                        const menuItems = [];
                        
                        // 利用可能なモデルがある場合
                        if (availableEmbeddingModels && availableEmbeddingModels.length > 0) {
                          availableEmbeddingModels.forEach(model => {
                            menuItems.push(
                              <MenuItem key={model} value={model}>
                                {model}
                              </MenuItem>
                            );
                          });
                          
                          // 現在のモデル名がリストにない場合、追加して表示
                          if (embeddingConfig.model_name && 
                              embeddingConfig.model_name.trim() !== '' && 
                              !availableEmbeddingModels.includes(embeddingConfig.model_name)) {
                            menuItems.unshift(
                              <MenuItem key={embeddingConfig.model_name} value={embeddingConfig.model_name}>
                                {embeddingConfig.model_name}
                              </MenuItem>
                            );
                          }
                        } else {
                          // 利用可能なモデルがない場合は、現在のモデル名を表示せず、
                          // 「利用可能なモデルがありません」のみ表示
                          menuItems.push(
                            <MenuItem key="no-models" value="" disabled>
                              利用可能なモデルがありません
                            </MenuItem>
                          );
                        }
                        
                        return menuItems;
                      })()}
                    </Select>
                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                      <IconButton onClick={handleRefreshEmbeddingModels} size="small">
                        <RefreshIcon />
                      </IconButton>
                      <Typography variant="caption" color="text.secondary">
                        利用可能なモデルを更新
                      </Typography>
                      <Typography variant="caption" color="info.main" sx={{ ml: 2 }}>
                        現在のモデル数: {availableEmbeddingModels ? availableEmbeddingModels.length : 0}
                      </Typography>
                    </Box>
                    {(!availableEmbeddingModels || availableEmbeddingModels.length === 0) && (
                      <Typography variant="caption" color="error" sx={{ mt: 1 }}>
                        {embeddingConfig.provider === 'openai' 
                          ? 'APIキーを確認してください' 
                          : 'APIキーまたはAPIベースURLを確認してください'
                        }
                      </Typography>
                    )}
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="ベクトル次元数"
                    type="number"
                    value={embeddingConfig.dimension}
                    onChange={e =>
                      handleEmbeddingInputChange('dimension', parseInt(e.target.value) || 1)
                    }
                    inputProps={{ min: 1 }}
                    helperText="埋め込みベクトルの次元数"
                    disabled={!isDimensionEditable}
                    InputProps={{
                      endAdornment: (
                        <IconButton 
                          size="small" 
                          onClick={() => setDimensionDialogOpen(true)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      ),
                    }}
                  />
                  {isDimensionEditable && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>重要警告:</strong> この値を変更すると既存のベクターデータベースにアクセスできなくなります。
                        変更する前に必ずベクターデータベースのバックアップを作成してください。
                        変更後はベクターデータベースを再作成する必要があります。
                      </Typography>
                    </Alert>
                  )}
                </Grid>
              </Grid>

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={handleSaveEmbeddingConfig}
                  disabled={isLoading}
                >
                  保存
                </Button>

                <Button
                  variant="outlined"
                  onClick={handleResetEmbeddingConfig}
                  disabled={isLoading}
                >
                  デフォルトにリセット
                </Button>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  設定テスト
                </Typography>

                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={isTesting ? <CircularProgress size={20} /> : <CheckIcon />}
                  onClick={handleTestEmbeddingConfig}
                  disabled={
                    isTesting ||
                    !embeddingConfig?.base_url ||
                    !embeddingConfig?.model_name ||
                    !embeddingConfig?.provider ||
                    embeddingConfig?.model_name.trim() === ''
                  }
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  テスト実行
                </Button>

                {testStatus !== 'idle' && (
                  <Alert
                    severity={testStatus}
                    icon={testStatus === 'success' ? <CheckIcon /> : testStatus === 'error' ? <ErrorIcon /> : undefined}
                    sx={{ mb: 2 }}
                  >
                    {testMessage}
                  </Alert>
                )}

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBottom>
                  現在の設定
                </Typography>

                <Box sx={{ fontSize: '0.875rem' }}>
                  <Typography variant="body2">
                    <strong>プロバイダー:</strong> {embeddingConfig?.provider}
                  </Typography>
                  <Typography variant="body2">
                    <strong>API Base:</strong> {embeddingConfig?.base_url}
                  </Typography>
                  <Typography variant="body2">
                    <strong>モデル:</strong> {embeddingConfig?.model_name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>次元数:</strong> {embeddingConfig?.dimension}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* ベクトル次元数変更確認ポップアップ */}
      <Dialog
        open={dimensionChangeConfirmOpen}
        onClose={() => setDimensionChangeConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" sx={{ color: 'warning.main' }}>
              ⚠️ ベクトル次元数の変更確認
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body1" paragraph>
              <strong>ベクトル次元数の変更を検出:</strong>
            </Typography>
            <Typography variant="body2" component="div" sx={{ ml: 2 }}>
              <ul>
                <li>次元数を {originalEmbeddingConfig?.dimension} から {embeddingConfig?.dimension} に変更します</li>
                <li>ベクトルデータベースが自動的に再作成されます</li>
                <li>既存のナレッジベースデータはすべて削除されます</li>
                <li>変更後はドキュメントを再アップロードする必要があります</li>
              </ul>
            </Typography>
            <Typography variant="body2" paragraph sx={{ mt: 2 }}>
              この操作は元に戻せません。続行しますか？
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleCancelDimensionChange}
            variant="outlined"
          >
            いいえ
          </Button>
          <Button 
            onClick={handleConfirmDimensionChange}
            variant="contained"
            color="warning"
          >
            はい
          </Button>
        </DialogActions>
      </Dialog>

      {/* ベクトル次元数編集確認ダイアログ */}
      <Dialog
        open={dimensionDialogOpen}
        onClose={() => setDimensionDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" sx={{ color: 'warning.main' }}>
              ⚠️ ベクトル次元数の変更確認
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body1" paragraph>
              <strong>重要警告:</strong> ベクトル次元数を変更すると、以下の影響があります：
            </Typography>
            <Typography variant="body2" component="div" sx={{ ml: 2 }}>
              <ul>
                <li>既存のベクターデータベースにアクセスできなくなります</li>
                <li>現在のナレッジベースデータが失われます</li>
                <li>変更後はベクターデータベースを再作成する必要があります</li>
              </ul>
            </Typography>
            <Typography variant="body2" paragraph sx={{ mt: 2 }}>
              変更を続行する前に、必ずベクターデータベースのバックアップを作成してください。
            </Typography>
          </Alert>
          <Typography variant="body2">
            本当にベクトル次元数を変更可能にしますか？
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setDimensionDialogOpen(false)}
            variant="outlined"
          >
            キャンセル
          </Button>
          <Button 
            onClick={() => {
              setDimensionDialogOpen(false);
              setIsDimensionEditable(true);
              enqueueSnackbar('ベクトル次元数を変更可能にしました', { variant: 'warning' });
            }}
            variant="contained"
            color="warning"
          >
            了解して変更可能にする
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LlmConfigPage;
