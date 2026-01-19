/**
 * ARS Flow動的フォームコンポーネント
 * MUI (Material-UI)ベース
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  FormHelperText,
} from '@mui/material';
import { ARSParam } from '../utils/arsFormConverter';

interface ARSFlowFormProps {
  flowId: string;
  flowName: string;
  params: ARSParam[];
  onSubmit: (flowId: string, values: Record<string, any>) => Promise<void>;
  onCancel?: () => void;
}

export const ARSFlowForm: React.FC<ARSFlowFormProps> = ({
  flowId,
  flowName,
  params,
  onSubmit,
  onCancel,
}) => {
  const [formValues, setFormValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleChange = (paramName: string, value: any) => {
    setFormValues(prev => ({
      ...prev,
      [paramName]: value,
    }));
    
    // エラーをクリア
    if (errors[paramName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[paramName];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    params.forEach(param => {
      if (param.required && !formValues[param.api_param_name]) {
        newErrors[param.api_param_name] = `${param.api_param_name}は必須です`;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      await onSubmit(flowId, formValues);
    } catch (error) {
      console.error('Flow execution error:', error);
      setSubmitError(
        error instanceof Error ? error.message : 'Flowの実行中にエラーが発生しました'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (param: ARSParam) => {
    const { api_param_name, param_type, option } = param;
    const value = formValues[api_param_name] || '';
    const error = errors[api_param_name];

    switch (param_type) {
      case 'text':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={submitting}
            variant="outlined"
            size="small"
          />
        );

      case 'number':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            type="number"
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={submitting}
            variant="outlined"
            size="small"
          />
        );

      case 'option':
        return (
          <FormControl
            key={api_param_name}
            fullWidth
            error={!!error}
            disabled={submitting}
            size="small"
          >
            <InputLabel>{api_param_name}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleChange(api_param_name, e.target.value)}
              label={api_param_name}
            >
              {option?.map((opt) => (
                <MenuItem key={opt.option_value} value={opt.option_value}>
                  {opt.option_label}
                </MenuItem>
              ))}
            </Select>
            {error && <FormHelperText>{error}</FormHelperText>}
          </FormControl>
        );

      case 'date':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            type="date"
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={submitting}
            variant="outlined"
            size="small"
            InputLabelProps={{
              shrink: true,
            }}
          />
        );

      default:
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={submitting}
            variant="outlined"
            size="small"
          />
        );
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2.5,
        backgroundColor: '#f5f5f5',
        borderRadius: 2,
        maxWidth: 500,
      }}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📋 {flowName}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          以下のパラメータを入力してください
        </Typography>

        {submitError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {submitError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {params.map(param => renderField(param))}
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mt: 3 }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : null}
          >
            {submitting ? '実行中...' : '実行'}
          </Button>
          
          {onCancel && (
            <Button
              variant="outlined"
              color="secondary"
              onClick={onCancel}
              disabled={submitting}
              sx={{ minWidth: 100 }}
            >
              キャンセル
            </Button>
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
          Flow ID: {flowId}
        </Typography>
      </Box>
    </Paper>
  );
};
