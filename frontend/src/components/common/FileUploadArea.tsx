import React, { useCallback } from 'react';
import { Box, Paper, Typography, IconButton, useTheme } from '@mui/material';
import { CloudUpload, Delete } from '@mui/icons-material';

interface FileUploadAreaProps {
  onFileSelect: (files: FileList) => void;
  acceptedFiles?: string;
  maxFiles?: number;
  maxSize?: number; // in MB
  title?: string;
  description?: string;
  selectedFiles?: File[];
  onFileRemove?: (index: number) => void;
}

const FileUploadArea: React.FC<FileUploadAreaProps> = ({
  onFileSelect,
  acceptedFiles = '*',
  maxFiles = 1,
  maxSize = 10,
  title = 'ファイルアップロード',
  description = 'クリックまたはドラッグ＆ドロップでファイルをアップロード',
  selectedFiles = [],
  onFileRemove,
}) => {
  const theme = useTheme();

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const { files } = e.dataTransfer;
      if (files.length > 0) {
        onFileSelect(files);
      }
    },
    [onFileSelect],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const { files } = e.target;
      if (files && files.length > 0) {
        onFileSelect(files);
      }
    },
    [onFileSelect],
  );

  const handleFileInputClick = useCallback(() => {
    document.getElementById('file-input')?.click();
  }, []);

  const handleFileRemove = useCallback(
    (index: number) => (e: React.MouseEvent) => {
      e.stopPropagation();
      onFileRemove?.(index);
    },
    [onFileRemove],
  );

  const formatFileSize = useCallback((bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }, []);

  // アップロードエリアコンポーネント
  const UploadArea = () => (
    <Paper
      sx={{
        border: `2px dashed ${theme.palette.divider}`,
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.action.hover,
        },
      }}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={handleFileInputClick}
    >
      <input
        id="file-input"
        type="file"
        accept={acceptedFiles}
        multiple={maxFiles > 1}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
      <CloudUpload sx={{ fontSize: 48, color: theme.palette.primary.main, mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        最大 {maxFiles} ファイル、{maxSize}MB まで
      </Typography>
    </Paper>
  );

  // ファイルリストコンポーネント
  const FileList = () => (
    <Box mt={2}>
      <Typography variant="subtitle2" gutterBottom>
        選択されたファイル:
      </Typography>
      {selectedFiles.map((file, index) => (
        <Box
          key={`${file.name}-${file.size}-${index}`}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 1,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 1,
            mb: 1,
          }}
        >
          <Box>
            <Typography variant="body2">{file.name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {formatFileSize(file.size)}
            </Typography>
          </Box>
          {onFileRemove && (
            <IconButton size="small" onClick={handleFileRemove(index)}>
              <Delete fontSize="small" />
            </IconButton>
          )}
        </Box>
      ))}
    </Box>
  );

  return (
    <Box>
      <UploadArea />
      {selectedFiles.length > 0 && <FileList />}
    </Box>
  );
};

export default FileUploadArea;
