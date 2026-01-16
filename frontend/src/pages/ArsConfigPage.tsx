import React, { useState, useEffect } from 'react';
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
  Divider,
  Alert,
  Link,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  HelpOutline as HelpIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

interface ArsConfig {
  apiKey: string;
  apiEndpoint?: string;
  timeout?: number;
  retryCount?: number;
}

const ArsConfigPage: React.FC = () => {
  const [config, setConfig] = useState<ArsConfig>({
    apiKey: '',
    apiEndpoint: '',
    timeout: 30,
    retryCount: 3,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  // 初期データの読み込み
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/ars-settings');
      if (response.data) {
        setConfig(response.data);
      } else {
        // デフォルト設定をセット
        setConfig({
          apiKey: '',
          apiEndpoint: 'http://localhost:5050',
          timeout: 30,
          retryCount: 3,
        });
      }
    } catch (error) {
      console.error('ARS設定の読み込みに失敗しました:', error);
      // エラー時にデフォルト設定をセット
      setConfig({
        apiKey: '',
        apiEndpoint: 'http://localhost:5050',
        timeout: 30,
        retryCount: 3,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof ArsConfig, value: string | number) => {
    setConfig(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSaveConfig = async () => {
    if (!config.apiKey || config.apiKey.trim() === '') {
      enqueueSnackbar('APIキーを入力してください', { variant: 'warning' });
      return;
    }

    setIsSaving(true);
    try {
      await axios.post('/api/ars-settings', config);
      enqueueSnackbar('ARS設定を保存しました', { variant: 'success' });
    } catch (error) {
      console.error('ARS設定の保存に失敗しました:', error);
      enqueueSnackbar('ARS設定の保存中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.apiKey || config.apiKey.trim() === '') {
      enqueueSnackbar('APIキーを入力してください', { variant: 'warning' });
      return;
    }

    setIsTesting(true);
    try {
      await axios.post('/api/ars-settings/test', config);
      enqueueSnackbar('ARS接続テストに成功しました', { variant: 'success' });
    } catch (error) {
      console.error('ARS接続テストに失敗しました:', error);
      enqueueSnackbar('ARS接続テストに失敗しました', { variant: 'error' });
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          ARS 設定
        </Typography>
        <IconButton
          href="https://docs.example.com/ars-settings"
          target="_blank"
          rel="noopener noreferrer"
          color="primary"
          title="ヘルプドキュメント"
        >
          <HelpIcon />
        </IconButton>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>ARS (Application Resource Service) について:</strong>
          <br />
          ARSは外部アプリケーションリソースサービスとの連携を管理します。
          APIキーを設定することで、ARSの機能を利用できるようになります。
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              基本設定
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="API Key"
                  value={config.apiKey}
                  onChange={e => handleInputChange('apiKey', e.target.value)}
                  placeholder="APIキーを入力してください"
                  type="password"
                  helperText="ARS APIのキー（必須）。ARSダッシュボードから取得できます。"
                />
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  詳細設定（オプション）
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="API エンドポイント"
                  value={config.apiEndpoint}
                  onChange={e => handleInputChange('apiEndpoint', e.target.value)}
                  placeholder="http://localhost:5050"
                  helperText="ARS APIのエンドポイントURL（デフォルト: http://localhost:5050）"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="タイムアウト (秒)"
                  type="number"
                  value={config.timeout}
                  onChange={e => handleInputChange('timeout', parseInt(e.target.value) || 30)}
                  inputProps={{ min: 1, max: 300 }}
                  helperText="API呼び出しのタイムアウト時間"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="リトライ回数"
                  type="number"
                  value={config.retryCount}
                  onChange={e => handleInputChange('retryCount', parseInt(e.target.value) || 3)}
                  inputProps={{ min: 0, max: 10 }}
                  helperText="失敗時のリトライ回数"
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={isSaving ? <CircularProgress size={20} /> : <SaveIcon />}
                onClick={handleSaveConfig}
                disabled={isSaving || isTesting}
              >
                保存
              </Button>

              <Button
                variant="outlined"
                startIcon={isTesting ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={handleTestConnection}
                disabled={isSaving || isTesting}
              >
                接続テスト
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                現在の設定
              </Typography>

              <Box sx={{ fontSize: '0.875rem', mb: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>APIキー:</strong> {config.apiKey ? '設定済み ●●●●●●' : '未設定'}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>エンドポイント:</strong> {config.apiEndpoint || 'デフォルト'}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>タイムアウト:</strong> {config.timeout}秒
                </Typography>
                <Typography variant="body2">
                  <strong>リトライ回数:</strong> {config.retryCount}回
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                設定ガイド
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                1. ARSダッシュボードからAPIキーを取得
                <br />
                2. 上記フォームにAPIキーを入力
                <br />
                3. 必要に応じて詳細設定を調整
                <br />
                4. 「保存」ボタンをクリック
                <br />
                5. 「接続テスト」で動作確認
              </Typography>

              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>注意:</strong> APIキーは機密情報です。
                  第三者と共有しないでください。
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ArsConfigPage;
