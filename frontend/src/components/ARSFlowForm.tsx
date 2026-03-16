/**
 * ARS Flow動的フォームコンポーネント
 * MUI (Material-UI)ベース
 */

import React, { useState, useEffect } from 'react';
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
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ARSParam } from '../utils/arsFormConverter';
import { FormStatus } from '../services/formStatusService';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import { FileUploadField, FileInfo } from './FileUploadField';

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
  const { user } = useAuth();
  const [formValues, setFormValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // ログインユーザー情報 + SSflowプロキシAPIで社員情報を自動セット
  useEffect(() => {
    if (!user || formStatus !== 'pending') return;

    const fillAutoFields = async () => {
      const autoValues: Record<string, any> = {
        content_empno:       user.username  || '',
        content_name:        user.full_name || user.username || '',
        AgentMode:           '0',
        AutoApprovalMode:    'N',
        AFFILIATION_COMPANY: '00000',
      };

      try {
        const token = authService.getAccessToken();
        const API_BASE = import.meta.env.VITE_API_URL || '';
        const res = await fetch(
          `${API_BASE}/api/users/employee-info?username=${encodeURIComponent(user.username)}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          const data = await res.json();
          if (data.full_name)        autoValues['content_name']           = data.full_name;
          if (data.company_name)     autoValues['content_company']        = data.company_name;
          if (data.department_name)  autoValues['content_dept']           = data.department_name;
          if (data.company_code)     autoValues['AFFILIATION_KAISHACODE'] = data.company_code;
          if (data.busho_code)       autoValues['AFFILIATION_BUSHOCODE']  = data.busho_code;
        }
      } catch (_) {
        // SSflow未接続時はデフォルト値のまま
      }

      setFormValues(prev => ({ ...autoValues, ...prev }));
    };

    fillAutoFields();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.username, flowId]);

  // initialValuesが変更されたらformValuesを更新（ただし既存のユーザー入力値は保持）
  useEffect(() => {
    if (initialValues && Object.keys(initialValues).length > 0) {
      setFormValues(prev => ({ ...initialValues, ...prev }));
    }
  }, [initialValues]);
  
  const isEditable = formStatus === 'pending';
  const isReadonly = !isEditable;
  
  console.log('[ARSFlowForm] Rendering:', { flowId, flowName, paramsCount: params.length, formStatus });

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

    // paramsのrequiredチェック（既存ロジック）
    params.forEach(param => {
      if (param.required && !formValues[param.api_param_name]) {
        newErrors[param.api_param_name] = `${param.label || param.api_param_name}は必須です`;
      }
    });

    // FK_Flow（申請フロー）必須チェック
    const fkFlow = (formValues['FK_Flow'] || '').toString().trim();
    if (!fkFlow) {
      newErrors['FK_Flow'] = '申請フローを選択してください';
    }

    // 申請内容（COMMENT）必須チェック
    const comment = (formValues['COMMENT'] || '').toString().trim();
    if (!comment) {
      newErrors['COMMENT'] = '申請内容を入力してください';
    }

    // 申請サマリー（氏名・会社名・所属）必須チェック
    if (!(formValues['content_name'] || '').toString().trim()) {
      newErrors['content_name'] = '氏名は必須です';
    }
    if (!(formValues['content_company'] || '').toString().trim()) {
      newErrors['content_company'] = '会社名称は必須です';
    }
    if (!(formValues['content_dept'] || '').toString().trim()) {
      newErrors['content_dept'] = '所属は必須です';
    }

    // 所属情報（KAISHACODE・BUSHOCODE）必須 + 数字のみチェック
    const kaishaCode = (formValues['AFFILIATION_KAISHACODE'] || '').toString().trim();
    if (!kaishaCode) {
      newErrors['AFFILIATION_KAISHACODE'] = '会社コードは必須です';
    } else if (!/^\d+$/.test(kaishaCode)) {
      newErrors['AFFILIATION_KAISHACODE'] = '会社コードは数字のみ入力してください';
    }

    const bushoCode = (formValues['AFFILIATION_BUSHOCODE'] || '').toString().trim();
    if (!bushoCode) {
      newErrors['AFFILIATION_BUSHOCODE'] = '部署コードは必須です';
    } else if (!/^\d+$/.test(bushoCode)) {
      newErrors['AFFILIATION_BUSHOCODE'] = '部署コードは数字のみ入力してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const assembleMaintblnameValue = (values: Record<string, any>): Record<string, any> => {
    const result = { ...values };

    const summryObj = {
      AgentMode:        result['AgentMode'] || '0',
      AutoApprovalMode: result['AutoApprovalMode'] || 'N',
      content: [
        { name: '従業員氏名', value: result['content_name']    || '' },
        { name: '社員番号',   value: result['content_empno']   || '' },
        { name: '会社名称',   value: result['content_company'] || '' },
        { name: '所属',       value: result['content_dept']    || '' },
      ],
    };

    const affiliationObj = {
      APPLICANT_AFFILIATION: {
        COMPANY:    result['AFFILIATION_COMPANY']    || '00000',
        KAISHACODE: result['AFFILIATION_KAISHACODE'] || '',
        BUSHOCODE:  result['AFFILIATION_BUSHOCODE']  || '',
      },
    };

    result['MainTblName_value'] = JSON.stringify({
      COMMENT:          result['COMMENT']      || '',
      SUMMRY:           JSON.stringify(summryObj),
      AFFILIATION_INFO: affiliationObj,
      UPLOAD_FILES:     result['UPLOAD_FILES'] || '[]',
    });

    [
      'COMMENT', 'AgentMode', 'AutoApprovalMode',
      'content_name', 'content_empno', 'content_company', 'content_dept',
      'AFFILIATION_COMPANY', 'AFFILIATION_KAISHACODE', 'AFFILIATION_BUSHOCODE',
      'UPLOAD_FILES',
    ].forEach(k => delete result[k]);

    return result;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      const assembled = assembleMaintblnameValue(formValues);
      await onSubmit(flowId, assembled);
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

  // フォームに表示しない（自動セット済みのシステムフィールド）
  const HIDDEN_FIELDS = new Set(['content_empno', 'AgentMode', 'AutoApprovalMode']);

  const renderGroupField = (param: ARSParam, accordion = false): React.ReactNode => {
    if (!param.children) return null;
    const visibleChildren = param.children.filter(c => !HIDDEN_FIELDS.has(c.api_param_name));
    if (visibleChildren.length === 0) return null;

    const childrenContent = (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {visibleChildren.map(child => {
          if (child.param_type === 'summry_group' || child.param_type === 'affiliation_group') {
            return renderGroupField(child);
          }
          if (child.param_type === 'upload' || child.api_param_name === 'UPLOAD_FILES') {
            return renderUploadField(child);
          }
          return renderField(child);
        })}
      </Box>
    );

    if (accordion) {
      // 申請内容グループ内のフィールドにエラーがあるか確認
      const MAINTBL_ERROR_FIELDS = [
        'COMMENT', 'content_name', 'content_company', 'content_dept',
        'AFFILIATION_KAISHACODE', 'AFFILIATION_BUSHOCODE',
      ];
      const hasInnerError = MAINTBL_ERROR_FIELDS.some(f => !!errors[f]);

      return (
        <Accordion
          key={param.api_param_name}
          defaultExpanded={false}
          disableGutters
          sx={{
            boxShadow: 'none',
            border: hasInnerError ? '1.5px solid #d32f2f' : '1px solid #e0e0e0',
            borderRadius: '8px !important',
            '&:before': { display: 'none' },
            backgroundColor: isReadonly ? '#f9f9f9' : '#ffffff',
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon fontSize="small" />}
            sx={{
              minHeight: 40,
              px: 1.5,
              '& .MuiAccordionSummary-content': { my: 0.5 },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <Typography variant="caption" sx={{ fontWeight: 600, color: hasInnerError ? 'error.main' : 'text.secondary' }}>
                {param.label || param.api_param_name}
              </Typography>
              {hasInnerError && (
                <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 500 }}>
                  ⚠ 未入力または入力エラーがあります
                </Typography>
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0, pb: 1.5, px: 1.5 }}>
            {childrenContent}
          </AccordionDetails>
        </Accordion>
      );
    }

    return (
      <Box key={param.api_param_name} sx={{ mt: 0.5 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mb: 0.5, fontWeight: 600, borderBottom: '1px solid #e0e0e0', pb: 0.5 }}
        >
          {param.label || param.api_param_name}
        </Typography>
        <Box sx={{ pl: 1 }}>
          {childrenContent}
        </Box>
      </Box>
    );
  };

  const renderUploadField = (param: ARSParam): React.ReactNode => {
    const { api_param_name, label } = param;
    const displayLabel = label || api_param_name;
    const rawVal = formValues[api_param_name];

    let fileItems: FileInfo[] = [];
    try {
      const parsed = rawVal ? JSON.parse(rawVal) : [];
      if (Array.isArray(parsed)) {
        fileItems = parsed;
      }
    } catch (_) { 
      fileItems = []; 
    }

    const handleFilesChange = (files: FileInfo[]) => {
      handleChange(api_param_name, JSON.stringify(files));
    };

    return (
      <Box key={api_param_name}>
        <FileUploadField
          value={fileItems}
          onChange={handleFilesChange}
          maxFiles={5}
          maxSizeMB={10}
          disabled={!isEditable || submitting}
          label={displayLabel}
        />
      </Box>
    );
  };

  const renderField = (param: ARSParam): React.ReactNode => {
    if (param.param_type === 'group') return renderGroupField(param, param.api_param_name === 'MainTblName_value');
    // 明示的に非表示指定されたフィールド（バッジ or システム値として自動セット済み）
    if (HIDDEN_FIELDS.has(param.api_param_name)) return null;
    // UPLOAD_FILES は専用UIで描画
    if (param.api_param_name === 'UPLOAD_FILES') return renderUploadField(param);

    const { api_param_name, param_type, label, option } = param;
    const displayLabel = label || api_param_name;
    const value = formValues[api_param_name] ?? (param.default_value ?? '');
    const error = errors[api_param_name];

    switch (param_type) {
      case 'textarea':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={displayLabel}
            multiline
            rows={3}
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{ readOnly: isReadonly }}
          />
        );

      case 'text':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={displayLabel}
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
            label={displayLabel}
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
            <InputLabel>{displayLabel}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleChange(api_param_name, e.target.value)}
              label={displayLabel}
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
            label={displayLabel}
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
            label={displayLabel}
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
            パラメータが送信されました。実行結果をお待ちください...
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
            実行が完了しました。
          </Alert>
        );
      case 'error':
        return (
          <Alert severity="error" sx={{ mt: 2 }}>
            実行中にエラーが発生しました。
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
        width: '100%',
        opacity: isReadonly ? 0.9 : 1,
      }}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📋 {flowName}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {isEditable ? '以下のパラメータを入力してください' : 'パラメータ（読み取り専用）'}
        </Typography>

        {/* 自動入力ユーザー情報バッジ */}
        {user && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mb: 2 }}>
            <Chip size="small" label={`社員番号: ${formValues['content_empno'] || user.username}`} color="primary" variant="outlined" />
            <Chip size="small" label={`氏名: ${formValues['content_name'] || user.full_name || user.username}`} variant="outlined" />
            {formValues['content_company'] && (
              <Chip size="small" label={`会社: ${formValues['content_company']}`} variant="outlined" />
            )}
            {formValues['content_dept'] && (
              <Chip size="small" label={`所属: ${formValues['content_dept']}`} variant="outlined" />
            )}
          </Box>
        )}

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
            {onCancel && (
              <Button
                variant="outlined"
                size="small"
                onClick={handleCancelClick}
                disabled={submitting}
                sx={{
                  minWidth: 88,
                  py: 0.5,
                  borderRadius: 1.5,
                  borderColor: 'grey.400',
                  color: 'text.secondary',
                  fontSize: '0.8rem',
                  '&:hover': { borderColor: 'grey.600', backgroundColor: 'grey.50' },
                }}
              >
                キャンセル
              </Button>
            )}
            <Button
              type="submit"
              variant="contained"
              size="small"
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={14} color="inherit" /> : null}
              sx={{
                flex: 1,
                py: 0.5,
                borderRadius: 1.5,
                fontWeight: 600,
                fontSize: '0.8rem',
                backgroundColor: '#1976d2',
                '&:hover': { backgroundColor: '#1565c0' },
                '&:disabled': { backgroundColor: 'grey.300' },
              }}
            >
              {submitting ? '実行中...' : '✔ 実行'}
            </Button>
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
          Flow ID: {flowId} | 状態: {formStatus}
        </Typography>
      </Box>
    </Paper>
  );
};
