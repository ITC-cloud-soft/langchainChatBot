import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Upload as UploadIcon,
  Folder as FolderIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';

import { knowledgeApi } from '../services/api';

interface Document {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
}

interface CollectionInfo {
  name: string;
  count: number;
  metadata: Record<string, unknown>;
}

const KnowledgePage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [collectionInfo, setCollectionInfo] = useState<CollectionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<
    Array<{
      content: string;
      similarity_score?: number;
    }>
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newDocumentContent, setNewDocumentContent] = useState('');
  const [metadataRows, setMetadataRows] = useState<{ id: string; key: string; value: string }[]>([
    { id: '1', key: '', value: '' },
  ]);
  const [metadataError, setMetadataError] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await knowledgeApi.listDocuments(rowsPerPage);
      setDocuments(response.documents);
    } catch (error: unknown) {
      console.error('Error loading documents:', error);
      const errorMessage =
        error instanceof Error ? error.message : 'ドキュメントの読み込み中にエラーが発生しました';
      enqueueSnackbar(errorMessage, { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  }, [rowsPerPage, enqueueSnackbar]);

  const loadCollectionInfo = useCallback(async () => {
    try {
      const response = await knowledgeApi.getCollectionInfo();
      setCollectionInfo(response);
    } catch (error: unknown) {
      console.error('Error loading collection info:', error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'コレクション情報の読み込み中にエラーが発生しました';
      enqueueSnackbar(errorMessage, { variant: 'error' });
    }
  }, [enqueueSnackbar]);

  // Load data on component mount
  useEffect(() => {
    loadDocuments();
    loadCollectionInfo();
  }, [loadDocuments, loadCollectionInfo]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const response = await knowledgeApi.searchKnowledge(searchQuery);
      setSearchResults(response.results);
    } catch (error) {
      console.error('Error searching knowledge:', error);
      enqueueSnackbar('ナレッジの検索中にエラーが発生しました', { variant: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!window.confirm('このドキュメントを削除してもよろしいですか？')) return;

    try {
      await knowledgeApi.deleteDocument(docId);
      enqueueSnackbar('ドキュメントを削除しました', { variant: 'success' });
      loadDocuments();
      loadCollectionInfo();
    } catch (error) {
      console.error('Error deleting document:', error);
      enqueueSnackbar('ドキュメントの削除中にエラーが発生しました', { variant: 'error' });
    }
  };

  const handleClearCollection = async () => {
    if (
      !window.confirm('すべてのドキュメントを削除してもよろしいですか？この操作は元に戻せません。')
    )
      return;

    try {
      await knowledgeApi.clearCollection();
      enqueueSnackbar('コレクションをクリアしました', { variant: 'success' });
      loadDocuments();
      loadCollectionInfo();
    } catch (error) {
      console.error('Error clearing collection:', error);
      enqueueSnackbar('コレクションのクリア中にエラーが発生しました', { variant: 'error' });
    }
  };

  const handleAddDocument = async () => {
    if (!newDocumentContent.trim()) {
      enqueueSnackbar('ドキュメントの内容を入力してください', { variant: 'warning' });
      return;
    }

    try {
      const metadata: Record<string, unknown> = {};
      // メタデータ行からJSONを生成
      const filledRows = metadataRows.filter(row => row.key.trim());
      if (filledRows.length > 0) {
        for (const row of filledRows) {
          if (!row.key.trim()) continue;

          // 値の型を自動判定
          const trimmedValue = row.value.trim();
          if (!trimmedValue) {
            metadata[row.key.trim()] = '';
          } else if (trimmedValue.toLowerCase() === 'true') {
            metadata[row.key.trim()] = true;
          } else if (trimmedValue.toLowerCase() === 'false') {
            metadata[row.key.trim()] = false;
          } else if (!isNaN(Number(trimmedValue))) {
            metadata[row.key.trim()] = Number(trimmedValue);
          } else {
            // 配列やオブジェクトとしてパースを試みる
            try {
              const parsed = JSON.parse(trimmedValue);
              metadata[row.key.trim()] = parsed;
            } catch {
              metadata[row.key.trim()] = trimmedValue;
            }
          }
        }
      }

      await knowledgeApi.addDocument({
        content: newDocumentContent,
        metadata,
      });

      enqueueSnackbar('ドキュメントを追加しました', { variant: 'success' });
      setIsAddDialogOpen(false);
      setNewDocumentContent('');
      setMetadataRows([{ id: '1', key: '', value: '' }]);
      setMetadataError('');
      loadDocuments();
      loadCollectionInfo();
    } catch (error) {
      console.error('Error adding document:', error);
      enqueueSnackbar('ドキュメントの追加中にエラーが発生しました', { variant: 'error' });
    }
  };

  const addMetadataRow = () => {
    setMetadataRows([...metadataRows, { id: Date.now().toString(), key: '', value: '' }]);
  };

  const removeMetadataRow = (id: string) => {
    if (metadataRows.length === 1) {
      setMetadataRows([{ id: Date.now().toString(), key: '', value: '' }]);
    } else {
      setMetadataRows(metadataRows.filter(row => row.id !== id));
    }
  };

  const updateMetadataRow = (id: string, field: 'key' | 'value', newValue: string) => {
    setMetadataRows(metadataRows.map(row => (row.id === id ? { ...row, [field]: newValue } : row)));
  };

  const validateMetadataRows = () => {
    // 重複キーのチェック
    const keys = metadataRows.filter(row => row.key.trim()).map(row => row.key.trim());

    const uniqueKeys = new Set(keys);
    if (keys.length !== uniqueKeys.size) {
      setMetadataError('重複するキーが存在します');
      return false;
    }

    setMetadataError('');
    return true;
  };

  const onDropFiles = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    try {
      const formData = new FormData();
      acceptedFiles.forEach(file => {
        formData.append('files', file);
      });

      // FileListを作成してAPIに渡す
      const fileList = new DataTransfer();
      acceptedFiles.forEach(file => fileList.items.add(file));
      await knowledgeApi.uploadDirectory(fileList.files);
      enqueueSnackbar(`${acceptedFiles.length}個のファイルをアップロードしました`, {
        variant: 'success',
      });
      loadDocuments();
      loadCollectionInfo();
    } catch (error) {
      console.error('Error uploading files:', error);
      enqueueSnackbar('ファイルのアップロード中にエラーが発生しました', { variant: 'error' });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropFiles,
    accept: {
      'text/plain': ['.txt'],
      'application/json': ['.json'],
      'text/markdown': ['.md'],
    },
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatMetadata = (metadata: Record<string, unknown>) => {
    return JSON.stringify(metadata, null, 2);
  };

  const truncateContent = (content: string, maxLength = 100) => {
    if (content.length <= maxLength) return content;
    return `${content.substring(0, maxLength)}...`;
  };

  return (
    <Box sx={{ height: '100%' }}>
      <Typography variant="h4" gutterBottom>
        ナレッジ設定
      </Typography>

      {collectionInfo && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography>
              現在のコレクション: {collectionInfo.name} ({collectionInfo.count} ドキュメント)
            </Typography>
          </Box>
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Box
              sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}
            >
              <Typography variant="h6">ドキュメント一覧</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => {
                    loadDocuments();
                    loadCollectionInfo();
                  }}
                  disabled={isLoading}
                >
                  更新
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={handleClearCollection}
                  disabled={isLoading || !collectionInfo || collectionInfo.count === 0}
                >
                  すべて削除
                </Button>
              </Box>
            </Box>

            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>内容</TableCell>
                        <TableCell>メタデータ</TableCell>
                        <TableCell>操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {documents
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map(doc => (
                          <TableRow key={doc.id}>
                            <TableCell>{doc.id}</TableCell>
                            <TableCell>
                              <Tooltip title={doc.content}>
                                <span>{truncateContent(doc.content)}</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <Tooltip title={formatMetadata(doc.metadata)}>
                                <span>{truncateContent(formatMetadata(doc.metadata), 50)}</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <IconButton
                                color="error"
                                onClick={() => handleDeleteDocument(doc.id)}
                                size="small"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  rowsPerPageOptions={[5, 10, 25]}
                  component="div"
                  count={documents.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={handleChangePage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                />
              </>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ドキュメントの追加
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setIsAddDialogOpen(true)}
                  fullWidth
                >
                  テキストを追加
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<UploadIcon />}
                  fullWidth
                  {...getRootProps()}
                  sx={{
                    bgcolor: isDragActive ? 'action.hover' : 'inherit',
                    border: isDragActive ? '2px dashed' : '1px solid',
                    borderColor: isDragActive ? 'primary.main' : 'divider',
                  }}
                >
                  <input {...getInputProps()} />
                  ファイルをアップロード
                </Button>

                <Button variant="outlined" startIcon={<FolderIcon />} fullWidth disabled>
                  ディレクトリを追加 (開発中)
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ナレッジの検索
              </Typography>

              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  label="検索クエリ"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  onKeyPress={e => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                />
                <IconButton
                  color="primary"
                  onClick={handleSearch}
                  disabled={isSearching || !searchQuery.trim()}
                >
                  {isSearching ? <CircularProgress size={24} /> : <SearchIcon />}
                </IconButton>
              </Box>

              {searchResults.length > 0 && (
                <Box>
                  <Typography variant="body2" gutterBottom>
                    検索結果 ({searchResults.length}件):
                  </Typography>
                  {searchResults.map((result, index) => (
                    <Card key={index} sx={{ mb: 1, p: 1 }}>
                      <Typography variant="body2">{truncateContent(result.content)}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        類似度: {result.similarity_score?.toFixed(4) ?? 'N/A'}
                      </Typography>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog
        open={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>ドキュメントの追加</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={6}
            label="ドキュメントの内容"
            value={newDocumentContent}
            onChange={e => setNewDocumentContent(e.target.value)}
            sx={{ mb: 2 }}
          />

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2, mb: 1 }}>
            メタデータ
          </Typography>

          {metadataRows.map(row => (
            <Box key={row.id} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
              <TextField
                label="キー"
                value={row.key}
                onChange={e => updateMetadataRow(row.id, 'key', e.target.value)}
                sx={{ flex: 1 }}
                placeholder="例: category"
                size="small"
              />
              <TextField
                label="値"
                value={row.value}
                onChange={e => updateMetadataRow(row.id, 'value', e.target.value)}
                sx={{ flex: 1 }}
                placeholder="例: general"
                size="small"
              />
              <IconButton
                onClick={() => removeMetadataRow(row.id)}
                color="error"
                size="small"
                disabled={metadataRows.length === 1}
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          ))}

          {metadataError && (
            <Typography color="error" variant="caption" sx={{ mb: 1 }}>
              {metadataError}
            </Typography>
          )}

          <Button onClick={addMetadataRow} startIcon={<AddIcon />} size="small" sx={{ mb: 2 }}>
            メタデータ行を追加
          </Button>

          <Typography variant="caption" color="text.secondary">
            ヒント: 値は自動的に型判定されます（true/false → 真偽値、数値 → 数値、JSON文字列 →
            オブジェクト/配列）
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setIsAddDialogOpen(false);
              setMetadataRows([{ id: '1', key: '', value: '' }]);
              setMetadataError('');
            }}
          >
            キャンセル
          </Button>
          <Button
            onClick={() => {
              if (validateMetadataRows()) {
                handleAddDocument();
              }
            }}
            variant="contained"
          >
            追加
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KnowledgePage;
