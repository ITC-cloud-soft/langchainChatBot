import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';

import createAppTheme from './themes';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import LlmConfigPage from './pages/LlmConfigPage';
import KnowledgePage from './pages/KnowledgePage';

// アプリケーションテーマの作成
const theme = createAppTheme('light');

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
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
              height: '100vh',
              maxHeight: '100vh',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/llm-config" element={<LlmConfigPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
            </Routes>
          </Container>
        </Layout>
      </Box>
    </ThemeProvider>
  );
}

export default App;
