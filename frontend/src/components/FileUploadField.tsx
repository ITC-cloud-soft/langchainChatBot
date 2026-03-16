import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  IconButton,
  LinearProgress,
  Alert,
  Paper,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material';
import { uploadFile, UploadFileResponse } from '../services/api';

export interface FileInfo {
  fileName: string;
  fileSize: string;
  azureName: string;
  azureFileName: string;
  containerName: string;
  uploadedAt?: string;
}

interface FileUploadFieldProps {
  value?: FileInfo[];
  onChange?: (files: FileInfo[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  disabled?: boolean;
  label?: string;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const extractBlobName = (url: string): string => {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/');
    return pathParts.slice(2).join('/');
  } catch {
    return url;
  }
};

export const FileUploadField: React.FC<FileUploadFieldProps> = ({
  value = [],
  onChange,
  maxFiles = 5,
  maxSizeMB = 10,
  disabled = false,
  label = 'ファイルを添付',
}) => {
  const [files, setFiles] = useState<FileInfo[]>(value);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    if (files.length + selectedFiles.length > maxFiles) {
      setError(`最大 ${maxFiles} 個のファイルまでアップロードできます`);
      return;
    }

    setError(null);
    setUploading(true);
    setUploadProgress(0);

    const uploadedFiles: FileInfo[] = [];
    const totalFiles = selectedFiles.length;
    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    for (let i = 0; i < totalFiles; i++) {
      const file = selectedFiles[i];

      if (file.size > maxSizeBytes) {
        setError(`${file.name} のサイズが上限 ${maxSizeMB}MB を超えています`);
        continue;
      }

      try {
        const response: UploadFileResponse = await uploadFile(file);

        const fileInfo: FileInfo = {
          fileName: response.name,
          fileSize: formatFileSize(file.size),
          azureName: response.url,
          azureFileName: extractBlobName(response.url),
          containerName: 'chatbot',
          uploadedAt: new Date().toISOString(),
        };

        uploadedFiles.push(fileInfo);
        setUploadProgress(((i + 1) / totalFiles) * 100);
      } catch (error: any) {
        console.error('ファイルアップロードエラー:', error);
        setError(`${file.name} のアップロードに失敗しました: ${error.response?.data?.detail || error.message}`);
      }
    }

    const newFiles = [...files, ...uploadedFiles];
    setFiles(newFiles);
    onChange?.(newFiles);
    setUploading(false);
    setUploadProgress(0);

    event.target.value = '';
  };

  const handleFileRemove = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onChange?.(newFiles);
  };

  React.useEffect(() => {
    setFiles(value);
  }, [value]);

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 500 }}>
        {label}
      </Typography>

      <Button
        variant="outlined"
        component="label"
        startIcon={<CloudUploadIcon />}
        disabled={uploading || disabled || files.length >= maxFiles}
        sx={{ mb: 2 }}
      >
        ファイルを選択
        <input
          type="file"
          hidden
          multiple
          onChange={handleFileSelect}
          disabled={uploading || disabled || files.length >= maxFiles}
        />
      </Button>

      {uploading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
            アップロード中... {Math.round(uploadProgress)}%
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {files.length > 0 && (
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            添付ファイル ({files.length}/{maxFiles})
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
            {files.map((file, index) => (
              <Paper
                key={index}
                variant="outlined"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  p: 1.5,
                  bgcolor: 'grey.50',
                  '&:hover': {
                    bgcolor: 'grey.100',
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
                  <Typography variant="caption" color="text.secondary">
                    {file.fileSize}
                  </Typography>
                </Box>
                {!disabled && (
                  <IconButton
                    size="small"
                    onClick={() => handleFileRemove(index)}
                    color="error"
                    aria-label="削除"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Paper>
            ))}
          </Box>
        </Box>
      )}

      {files.length === 0 && !uploading && (
        <Typography variant="caption" color="text.secondary">
          ファイルが選択されていません
        </Typography>
      )}
    </Box>
  );
};
