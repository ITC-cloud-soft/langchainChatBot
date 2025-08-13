import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, CssBaseline } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import LlmConfigPage from './pages/LlmConfigPage';
import KnowledgePage from './pages/KnowledgePage';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Layout>
          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
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
