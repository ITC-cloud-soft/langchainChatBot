/**
 * 承認・否認フォームダイアログ
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Divider,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as DenyIcon,
  Assignment as FormIcon,
  InsertDriveFile as FileIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { generateDownloadUrl } from '../services/api';
import { FileInfo } from './FileUploadField';

interface ApprovalFormDialogProps {
  open: boolean;
  onClose: () => void;
  notification: any;
  onActionComplete?: (action: 'approve' | 'deny', message: string) => void;
  backendUrl: string;
  authToken: string;
}

export default function ApprovalFormDialog({
  open,
  onClose,
  notification,
  onActionComplete,
  backendUrl,
  authToken,
}: ApprovalFormDialogProps) {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);

  const payload = notification?.payload || {};
  const arsParams = payload?.arsParams || payload?.workflowData;
  const createdAt = notification?._createdAt || notification?.createdAt;
  const formattedDate = createdAt
    ? new Date(createdAt).toLocaleString('ja-JP', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
      })
    : null;

  const getAttachedFiles = (): FileInfo[] => {
    console.log('[ApprovalFormDialog] arsParams:', arsParams);
    
    if (!arsParams) {
      console.log('[ApprovalFormDialog] arsParams is null/undefined');
      return [];
    }
    
    const files: FileInfo[] = [];
    
    Object.keys(arsParams).forEach(key => {
      console.log(`[ApprovalFormDialog] Checking key: ${key}, value:`, arsParams[key]);
      
      if (key === 'UPLOAD_FILES') {
        try {
          let fileData = arsParams[key];
          console.log('[ApprovalFormDialog] UPLOAD_FILES raw data:', fileData, 'type:', typeof fileData);
          
          if (typeof fileData === 'string') {
            fileData = JSON.parse(fileData);
            console.log('[ApprovalFormDialog] UPLOAD_FILES parsed:', fileData);
          }
          
          if (Array.isArray(fileData)) {
            console.log('[ApprovalFormDialog] Adding files:', fileData);
            files.push(...fileData);
          } else if (fileData && typeof fileData === 'object') {
            console.log('[ApprovalFormDialog] Adding single file:', fileData);
            files.push(fileData);
          }
        } catch (e) {
          console.error(`[ApprovalFormDialog] ${key} のパースに失敗:`, e);
        }
      }
    });
    
    console.log('[ApprovalFormDialog] Final files:', files);
    return files;
  };

  const handleDownloadFile = async (file: FileInfo) => {
    try {
      setDownloadingFile(file.azureFileName);
      setError(null);
      
      const response = await generateDownloadUrl(file.azureFileName, 1);
      
      window.open(response.download_url, '_blank');
    } catch (e: any) {
      console.error('ファイルダウンロードエラー:', e);
      setError(`ファイルのダウンロードに失敗しました: ${e.message}`);
    } finally {
      setDownloadingFile(null);
    }
  };

  const attachedFiles = getAttachedFiles();

  const handleAction = async (action: 'approve' | 'deny') => {
    if (!arsParams) {
      setError('承認に必要なパラメーターが見つかりません。SSFlowから再送信してください。');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resp = await fetch(`${backendUrl}/api/notifications/approval-action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          ars_params: arsParams,
          action,
          comment,
        }),
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || '処理に失敗しました');
      }

      const label = action === 'approve' ? '承認' : '否認';
      onActionComplete?.(action, data.message || `${label}が完了しました`);
      setComment('');
      onClose();
    } catch (e: any) {
      setError(e.message || '処理中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return;
    setComment('');
    setError(null);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2, boxShadow: '0 8px 32px rgba(0,0,0,0.12)' },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            承認リクエスト
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 1 }}>
        {/* 申請詳細 */}
        <Box
          sx={{
            backgroundColor: 'grey.50',
            borderRadius: 1.5,
            p: 2,
            mb: 2,
            border: '1px solid',
            borderColor: 'grey.200',
          }}
        >
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            申請内容
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>

            {/* メッセージ本文 */}
            {payload?.content && (
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: 'rgba(25, 118, 210, 0.05)',
                  borderRadius: 1,
                  borderLeft: '3px solid',
                  borderColor: 'primary.main',
                  mb: 0.5,
                }}
              >
                <Typography variant="body2" sx={{ color: 'text.primary', lineHeight: 1.6 }}>
                  {payload.content}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                フロー
              </Typography>
              <Chip
                label={payload?.flowName || '—'}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80, pt: 0.25 }}>
                申請者
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {payload?.starterName || '—'}
              </Typography>
            </Box>

            {payload?.comment && (
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80, pt: 0.25 }}>
                  コメント
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                  {payload.comment}
                </Typography>
              </Box>
            )}

            <Divider sx={{ my: 0.5 }} />

            {arsParams?.WorkID && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  申請番号
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                  {arsParams.WorkID}
                </Typography>
              </Box>
            )}

            {arsParams?.FK_Flow && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  フローID
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                  {arsParams.FK_Flow}
                </Typography>
              </Box>
            )}

            {arsParams?.FK_Node && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  ノードID
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                  {arsParams.FK_Node}
                </Typography>
              </Box>
            )}

            {formattedDate && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  通知日時
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {formattedDate}
                </Typography>
              </Box>
            )}

          </Box>
        </Box>

        {/* 添付ファイル */}
        {attachedFiles.length > 0 && (
          <>
            <Divider sx={{ my: 1.5 }} />
            
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mb: 1 }}>
                添付ファイル ({attachedFiles.length})
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {attachedFiles.map((file, index) => (
                  <Box
                    key={index}
                    onClick={() => handleDownloadFile(file)}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      p: 1.5,
                      bgcolor: 'grey.50',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'grey.200',
                      cursor: downloadingFile === file.azureFileName ? 'wait' : 'pointer',
                      transition: 'all 0.2s',
                      '&:hover': {
                        bgcolor: 'grey.100',
                        borderColor: 'primary.main',
                        transform: 'translateX(4px)',
                      },
                    }}
                  >
                    <FileIcon color="action" />
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 500,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {file.fileName}
                      </Typography>
                      {file.fileSize && (
                        <Typography variant="caption" color="text.secondary">
                          {file.fileSize}
                        </Typography>
                      )}
                    </Box>
                    {downloadingFile === file.azureFileName ? (
                      <CircularProgress size={20} />
                    ) : (
                      <DownloadIcon color="primary" />
                    )}
                  </Box>
                ))}
              </Box>
            </Box>
          </>
        )}

        <Divider sx={{ mb: 2 }} />

        {/* コメント入力 */}
        <TextField
          label="承認コメント（任意）"
          multiline
          rows={3}
          fullWidth
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={loading}
          placeholder="承認・否認の理由やコメントを入力してください"
          variant="outlined"
          size="small"
        />

        {/* エラー表示 */}
        {error && (
          <Typography
            variant="body2"
            color="error"
            sx={{ mt: 1.5, p: 1.5, backgroundColor: 'error.50', borderRadius: 1 }}
          >
            {error}
          </Typography>
        )}

        {/* arsParams 未設定の警告 */}
        {!arsParams && (
          <Typography
            variant="caption"
            color="warning.main"
            sx={{ mt: 1, display: 'block' }}
          >
            ※ この通知には承認パラメーターが含まれていません。SSFlowから再度申請を送信してください。
          </Typography>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2.5, gap: 1 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          color="inherit"
          sx={{ minWidth: 80 }}
        >
          キャンセル
        </Button>

        <Box sx={{ flex: 1 }} />

        <Button
          variant="outlined"
          color="error"
          startIcon={loading ? <CircularProgress size={16} /> : <DenyIcon />}
          onClick={() => handleAction('deny')}
          disabled={loading || !arsParams}
          sx={{ minWidth: 100 }}
        >
          否認
        </Button>

        <Button
          variant="contained"
          color="primary"
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <ApproveIcon />}
          onClick={() => handleAction('approve')}
          disabled={loading || !arsParams}
          sx={{ minWidth: 100 }}
        >
          承認
        </Button>
      </DialogActions>
    </Dialog>
  );
}
