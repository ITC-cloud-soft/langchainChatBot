/**
 * User Management Page
 * 
 * Admin page for managing users (single organization)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  PersonAdd as PersonAddIcon
} from '@mui/icons-material';
import { userService, User, CreateUserRequest, UpdateUserRequest } from '../services/userService';
import { useAuth } from '../contexts/AuthContext';

const UserManagementPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog states
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<User | null>(null);

  // Form state
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'user'
  });

  // Fetch users
  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await userService.getUsers(
        page + 1,
        rowsPerPage,
        roleFilter,
        search
      );

      setUsers(response.users);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ユーザーの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, rowsPerPage, roleFilter]);

  const handleSearch = () => {
    setPage(0);
    fetchUsers();
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleOpenDialog = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        full_name: user.full_name || '',
        role: user.role
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'user'
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
    setError(null);
  };

  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (editingUser) {
        // Update user
        const updateData: UpdateUserRequest = {
          email: formData.email,
          full_name: formData.full_name,
          role: formData.role
        };
        await userService.updateUser(editingUser.id, updateData);
        setSuccess('ユーザーを更新しました');
      } else {
        // Create new user
        await userService.createUser(formData);
        setSuccess('ユーザーを作成しました');
      }

      handleCloseDialog();
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteConfirm) return;

    try {
      setIsLoading(true);
      setError(null);

      await userService.deleteUser(deleteConfirm.id);
      setSuccess('ユーザーを削除しました');
      setDeleteConfirm(null);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ユーザーの削除に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleChip = (role: string) => {
    return role === 'admin' ? (
      <Chip label="管理者" color="primary" size="small" />
    ) : (
      <Chip label="ユーザー" color="default" size="small" />
    );
  };

  const getStatusChip = (isActive: boolean) => {
    return isActive ? (
      <Chip label="有効" color="success" size="small" />
    ) : (
      <Chip label="無効" color="error" size="small" />
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          ユーザー管理
        </Typography>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a4190 100%)'
            }
          }}
        >
          新規ユーザー作成
        </Button>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Search and Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            placeholder="ユーザー名、メールアドレスで検索"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyPress={handleSearchKeyPress}
            size="small"
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>ロール</InputLabel>
            <Select
              value={roleFilter}
              label="ロール"
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <MenuItem value="">全て</MenuItem>
              <MenuItem value="admin">管理者</MenuItem>
              <MenuItem value="user">ユーザー</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" onClick={handleSearch}>
            検索
          </Button>
        </Box>
      </Paper>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ユーザー名</TableCell>
              <TableCell>メールアドレス</TableCell>
              <TableCell>氏名</TableCell>
              <TableCell>ロール</TableCell>
              <TableCell>ステータス</TableCell>
              <TableCell>最終ログイン</TableCell>
              <TableCell align="right">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  ユーザーが見つかりません
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name || '-'}</TableCell>
                  <TableCell>{getRoleChip(user.role)}</TableCell>
                  <TableCell>{getStatusChip(user.is_active)}</TableCell>
                  <TableCell>
                    {user.last_login
                      ? new Date(user.last_login).toLocaleString('ja-JP')
                      : '-'}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(user)}
                      disabled={user.id === currentUser?.user_id}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => setDeleteConfirm(user)}
                      disabled={user.id === currentUser?.user_id}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="表示件数:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}件`}
        />
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'ユーザー編集' : '新規ユーザー作成'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="ユーザー名"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              disabled={!!editingUser}
              fullWidth
              required
            />
            <TextField
              label="メールアドレス"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              required
            />
            {!editingUser && (
              <TextField
                label="パスワード"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                fullWidth
                required
              />
            )}
            <TextField
              label="氏名"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>ロール</InputLabel>
              <Select
                value={formData.role}
                label="ロール"
                onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' })}
              >
                <MenuItem value="user">ユーザー</MenuItem>
                <MenuItem value="admin">管理者</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={isLoading}
          >
            {editingUser ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>ユーザー削除確認</DialogTitle>
        <DialogContent>
          <Typography>
            ユーザー「{deleteConfirm?.username}」を削除してもよろしいですか？
          </Typography>
          <Typography color="error" sx={{ mt: 1 }}>
            この操作は取り消せません。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>キャンセル</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained">
            削除
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagementPage;
