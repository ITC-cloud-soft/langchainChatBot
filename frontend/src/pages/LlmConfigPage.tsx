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
  status: 'success' | 'error';
  message: string;
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
  const [testStatus, setTestStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [dimensionDialogOpen, setDimensionDialogOpen] = useState(false);
  const [isDimensionEditable, setIsDimensionEditable] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

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
      const response = (await embeddingConfigApi.getConfig()) as EmbeddingConfigResponse;
      setEmbeddingConfig(response.config);
      // Also set available models from the config response
      if (response.available_models && Array.isArray(response.available_models)) {
        setAvailableEmbeddingModels(response.available_models);
      }
    } catch (error) {
      logger.error('Error loading embedding config:', error);
      const errorMessage =
        (error as Error).message || '埋め込み設定の読み込み中にエラーが発生しました';
      enqueueSnackbar(errorMessage, { variant: 'error' });
      // エラー時にデフォルト設定をセット
      setEmbeddingConfig({
        provider: 'ollama',
        base_url: 'http://localhost:11434',
        model_name: 'nomic-embed-text:latest',
        api_key: '',
        dimension: 768,
      });
    }
  }, [enqueueSnackbar]);

  const loadAvailableEmbeddingModels = useCallback(async () => {
    try {
      const response = await embeddingConfigApi.getAvailableModels();
      // Handle different response formats
      if (Array.isArray(response)) {
        setAvailableEmbeddingModels(response);
      } else if (response.data && Array.isArray(response.data)) {
        setAvailableEmbeddingModels(response.data);
      } else if (response.config?.available_models) {
        setAvailableEmbeddingModels(response.config.available_models);
      } else {
        logger.warn('Unexpected response format for embedding models:', response);
        setAvailableEmbeddingModels([]);
      }
    } catch (error) {
      logger.error('Error loading available embedding models:', error);
      enqueueSnackbar('利用可能な埋め込みモデルの読み込み中にエラーが発生しました', {
        variant: 'error',
      });
    }
  }, [enqueueSnackbar]);

  // Load config on component mount
  useEffect(() => {
    loadConfig();
    loadAvailableModels();
    loadEmbeddingConfig();
    loadAvailableEmbeddingModels();
  }, []); // Empty dependency array to run only on mount

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
      enqueueSnackbar('モデルリストを更新しました', { variant: 'success' });
    } catch (error) {
      logger.error('Error refreshing models:', error);
      enqueueSnackbar('モデルリストの更新中にエラーが発生しました', { variant: 'error' });
    }
  };

  const handleApiBaseChange = async (apiBase: string) => {
    if (!config) return;
    // Update config
    handleInputChange('api_base', apiBase);

    // Try to get models from the new API base
    if (apiBase && config.provider === 'カスタム') {
      try {
        const testConfig = {
          ...config,
          api_base: apiBase,
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
        enqueueSnackbar('新しいAPIからモデルリストを取得しました', { variant: 'success' });
      } catch (error) {
        logger.error('Error getting models from new API:', error);
        // Don't show error for automatic model fetching
      }
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

    // Only set defaults if the current values are empty or invalid
    let needsApiBaseUpdate = !embeddingConfig.base_url || embeddingConfig.base_url.trim() === '';
    let needsModelUpdate = !embeddingConfig.model_name || embeddingConfig.model_name.trim() === '';
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

    // Update API base, model name, and dimension only if needed
    if (needsApiBaseUpdate) {
      handleEmbeddingInputChange('base_url', newApiBase);
    }
    if (needsModelUpdate) {
      handleEmbeddingInputChange('model_name', newModelName);
    }
    if (needsDimensionUpdate) {
      handleEmbeddingInputChange('dimension', newDimension);
    }

    // Try to get models for the new provider
    if (provider === 'ollama' && newApiBase) {
      try {
        const testConfig = {
          ...embeddingConfig,
          provider: provider,
          base_url: newApiBase,
        };
        const response = await embeddingConfigApi.getAvailableModels();
        // Handle different response formats
        if (Array.isArray(response)) {
          setAvailableEmbeddingModels(response);
        } else if (response.data && Array.isArray(response.data)) {
          setAvailableEmbeddingModels(response.data);
        } else {
          setAvailableEmbeddingModels([]);
        }
        enqueueSnackbar(`${provider}の埋め込みモデルリストを取得しました`, { variant: 'success' });
      } catch (error) {
        logger.error('Error getting embedding models for new provider:', error);
        // Don't show error for automatic model fetching
      }
    } else {
      // For non-ollama providers, set the current model in available models
      if (newModelName) {
        setAvailableEmbeddingModels([newModelName]);
      }
    }
  };

  const handleEmbeddingApiBaseChange = async (apiBase: string) => {
    if (!embeddingConfig) return;
    // Update config
    handleEmbeddingInputChange('base_url', apiBase);

    // Try to get models from the new API base
    if (apiBase && embeddingConfig.provider === 'ollama') {
      try {
        const response = await embeddingConfigApi.getAvailableModels();
        // Handle different response formats
        if (Array.isArray(response)) {
          setAvailableEmbeddingModels(response);
        } else if (response.data && Array.isArray(response.data)) {
          setAvailableEmbeddingModels(response.data);
        } else {
          setAvailableEmbeddingModels([]);
        }
        enqueueSnackbar('新しいAPIから埋め込みモデルリストを取得しました', { variant: 'success' });
      } catch (error) {
        logger.error('Error getting embedding models from new API:', error);
        // Don't show error for automatic model fetching
      }
    }
  };

  const handleRefreshEmbeddingModels = async () => {
    if (!embeddingConfig) return;
    try {
      const response = await embeddingConfigApi.refreshAvailableModels();
      // Handle different response formats
      if (Array.isArray(response)) {
        setAvailableEmbeddingModels(response);
      } else if (response.data && Array.isArray(response.data)) {
        setAvailableEmbeddingModels(response.data);
      } else {
        setAvailableEmbeddingModels([]);
      }
      enqueueSnackbar('埋め込みモデルリストを更新しました', { variant: 'success' });
    } catch (error) {
      logger.error('Error refreshing embedding models:', error);
      enqueueSnackbar('埋め込みモデルリストの更新中にエラーが発生しました', { variant: 'error' });
    }
  };

  const handleSaveEmbeddingConfig = async () => {
    if (!embeddingConfig) return;
    setIsLoading(true);
    try {
      await embeddingConfigApi.updateConfig(embeddingConfig as unknown as Record<string, unknown>);
      enqueueSnackbar('埋め込み設定を保存しました', { variant: 'success' });
    } catch (error) {
      logger.error('Error saving embedding config:', error);
      enqueueSnackbar('埋め込み設定の保存中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
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
      setTestStatus(response.status === 'success' ? 'success' : 'error');
      setTestMessage(response.message);

      if (response.status === 'success') {
        enqueueSnackbar('埋め込み設定テストに成功しました', { variant: 'success' });
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
                    onChange={e => handleInputChange('api_key', e.target.value)}
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
                      {availableModels &&
                        availableModels.map(model => (
                          <MenuItem key={model} value={model}>
                            {model}
                          </MenuItem>
                        ))}
                    </Select>
                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                      <IconButton onClick={handleRefreshModels} size="small">
                        <RefreshIcon />
                      </IconButton>
                      <Typography variant="caption" color="text.secondary">
                        利用可能なモデルを更新
                      </Typography>
                    </Box>
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
                    severity={testStatus === 'success' ? 'success' : 'error'}
                    icon={testStatus === 'success' ? <CheckIcon /> : <ErrorIcon />}
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
                    </Typography>
                  </FormControl>
                </Grid>

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

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="API Key"
                    value={embeddingConfig.api_key}
                    onChange={e => handleEmbeddingInputChange('api_key', e.target.value)}
                    placeholder=""
                    type="password"
                    helperText="埋め込みAPIのキー（Ollamaの場合は不要）"
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>モデル名</InputLabel>
                    <Select
                      value={embeddingConfig.model_name}
                      label="モデル名"
                      onChange={e => handleEmbeddingInputChange('model_name', e.target.value)}
                    >
                      {availableEmbeddingModels &&
                        availableEmbeddingModels.map(model => (
                          <MenuItem key={model} value={model}>
                            {model}
                          </MenuItem>
                        ))}
                    </Select>
                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                      <IconButton onClick={handleRefreshEmbeddingModels} size="small">
                        <RefreshIcon />
                      </IconButton>
                      <Typography variant="caption" color="text.secondary">
                        利用可能なモデルを更新
                      </Typography>
                    </Box>
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
                    severity={testStatus === 'success' ? 'success' : 'error'}
                    icon={testStatus === 'success' ? <CheckIcon /> : <ErrorIcon />}
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
