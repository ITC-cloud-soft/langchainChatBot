import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Container, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';

import createAppTheme from './themes';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/auth/PrivateRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import LlmConfigPage from './pages/LlmConfigPage';
import KnowledgePage from './pages/KnowledgePage';
import UserManagementPage from './pages/UserManagementPage';
import ArsConfigPage from './pages/ArsConfigPage';

// アプリケーションテーマの作成
const theme = createAppTheme('light');

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          {/* Register route removed - only admin can create users */}

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: '100vh',
                  backgroundColor: 'background.default'
                }}>
                  <Layout>
                    <Container
                      maxWidth="xl"
                      sx={{
                        mt: 0,
                        mb: 0,
                        px: 0,
                        height: '100%',
                        maxHeight: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden'
                      }}
                    >
                      <Routes>
                        <Route path="/" element={<Navigate to="/chat" replace />} />
                        <Route path="/chat" element={<ChatPage />} />
                        
                        {/* Admin only routes */}
                        <Route
                          path="/llm-config"
                          element={
                            <PrivateRoute requireAdmin>
                              <LlmConfigPage />
                            </PrivateRoute>
                          }
                        />
                        <Route
                          path="/knowledge"
                          element={
                            <PrivateRoute requireAdmin>
                              <KnowledgePage />
                            </PrivateRoute>
                          }
                        />
                        <Route
                          path="/users"
                          element={
                            <PrivateRoute requireAdmin>
                              <UserManagementPage />
                            </PrivateRoute>
                          }
                        />
                        <Route
                          path="/ars-config"
                          element={
                            <PrivateRoute requireAdmin>
                              <ArsConfigPage />
                            </PrivateRoute>
                          }
                        />
                      </Routes>
                    </Container>
                  </Layout>
                </Box>
              </PrivateRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
