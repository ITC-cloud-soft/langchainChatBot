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
import { FormStatus } from '../services/formStatusService';

interface ARSFlowFormProps {
  flowId: string;
  flowName: string;
  params: ARSParam[];
  onSubmit: (flowId: string, values: Record<string, any>) => Promise<void>;
  onCancel?: () => void;
  formStatus?: FormStatus;
  initialValues?: Record<string, any>;
}

export const ARSFlowForm: React.FC<ARSFlowFormProps> = ({
  flowId,
  flowName,
  params,
  onSubmit,
  onCancel,
  formStatus = 'pending',
  initialValues = {},
}) => {
  const [formValues, setFormValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const isEditable = formStatus === 'pending';
  const isReadonly = !isEditable;

  const handleChange = (paramName: string, value: any) => {
    if (!isEditable) return;
    
    setFormValues(prev => ({
      ...prev,
      [paramName]: value,
    }));
    
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

  const handleCancelClick = () => {
    if (onCancel) {
      onCancel();
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
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
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
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );

      case 'option':
        return (
          <FormControl
            key={api_param_name}
            fullWidth
            error={!!error}
            disabled={!isEditable || submitting}
            size="small"
          >
            <InputLabel>{api_param_name}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleChange(api_param_name, e.target.value)}
              label={api_param_name}
              readOnly={isReadonly}
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
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputLabelProps={{
              shrink: true,
            }}
            InputProps={{
              readOnly: isReadonly,
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
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );
    }
  };

  const renderStatusMessage = () => {
    switch (formStatus) {
      case 'submitted':
        return (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✅ パラメータが送信されました。実行結果をお待ちください...
          </Alert>
        );
      case 'cancelled':
        return (
          <Alert severity="info" sx={{ mt: 2 }}>
            🚫 操作がキャンセルされました。入力内容は保持されています。
          </Alert>
        );
      case 'completed':
        return (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✅ 実行が完了しました。
          </Alert>
        );
      case 'error':
        return (
          <Alert severity="error" sx={{ mt: 2 }}>
            ❌ 実行中にエラーが発生しました。
          </Alert>
        );
      default:
        return null;
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2.5,
        backgroundColor: isReadonly ? '#fafafa' : '#f5f5f5',
        borderRadius: 2,
        maxWidth: 500,
        opacity: isReadonly ? 0.9 : 1,
      }}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📋 {flowName}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {isEditable ? '以下のパラメータを入力してください' : 'パラメータ（読み取り専用）'}
        </Typography>

        {submitError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {submitError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {params.map(param => renderField(param))}
        </Box>

        {renderStatusMessage()}

        {isEditable && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="small"
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={16} /> : null}
              sx={{ flex: 1, py: 0.75 }}
            >
              {submitting ? '実行中...' : '実行'}
            </Button>
          
          {onCancel && (
            <Button
              variant="outlined"
              color="secondary"
              size="small"
              onClick={handleCancelClick}
              disabled={submitting}
              sx={{ minWidth: 80, py: 0.75 }}
            >
              キャンセル
            </Button>
          )}
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
          Flow ID: {flowId} | 状態: {formStatus}
        </Typography>
      </Box>
    </Paper>
  );
};
