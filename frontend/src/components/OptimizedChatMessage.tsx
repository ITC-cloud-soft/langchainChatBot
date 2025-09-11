import React, { useState, memo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  alpha,
  useTheme,
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon, Source as SourceIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface OptimizedChatMessageProps {
  message: {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    sourceDocuments?: Array<{
      content: string;
      metadata: Record<string, unknown>;
    }>;
  };
  isLast: boolean;
}

// メモ化されたマークダウンコンポーネント
const MemoizedMarkdown: React.FC<{ content: string }> = memo(({ content }) => {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>;
});

MemoizedMarkdown.displayName = 'MemoizedMarkdown';

// メモ化されたソースドキュメントコンポーネント
const SourceDocuments: React.FC<{
  sourceDocuments: Array<{
    content: string;
    metadata: Record<string, unknown>;
  }>;
}> = memo(({ sourceDocuments }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Box sx={{ mt: 2 }}>
      <Accordion
        expanded={expanded}
        onChange={() => setExpanded(!expanded)}
        sx={{
          '&.MuiAccordion-root': {
            boxShadow: 'none',
            border: '1px solid',
            borderColor: 'divider',
            '&:before': {
              display: 'none',
            },
          },
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&.MuiAccordionSummary-root': {
              minHeight: 48,
              '&.Mui-expanded': {
                minHeight: 48,
              },
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SourceIcon sx={{ mr: 1, fontSize: 'small' }} />
            <Typography variant="body2">参照元 ({sourceDocuments.length})</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0 }}>
          {sourceDocuments.map((doc, docIndex) => (
            <Box
              key={docIndex}
              sx={{
                mb: 1,
                p: 1,
                backgroundColor: alpha('#000', 0.03),
                borderRadius: 1,
                borderLeft: '3px solid',
                borderColor: 'primary.main',
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  mb: 1,
                  lineHeight: 1.5,
                  color: 'text.primary',
                }}
              >
                {doc.content.length > 200 ? `${doc.content.substring(0, 200)}...` : doc.content}
              </Typography>
              {Object.keys(doc.metadata).length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      display: 'block',
                      mt: 0.5,
                    }}
                  >
                    メタデータ: {JSON.stringify(doc.metadata, null, 2)}
                  </Typography>
                </Box>
              )}
            </Box>
          ))}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
});

SourceDocuments.displayName = 'SourceDocuments';

const OptimizedChatMessage: React.FC<OptimizedChatMessageProps> = memo(({ message, isLast }) => {
  const theme = useTheme();

  // デバッグ用：メッセージをコンソールに出力
  React.useEffect(() => {
    // デバッグログを削除
  }, [message, isLast]);

  // タイムスタンプをフォーマット
  const formattedTime = React.useMemo(() => {
    try {
      return new Date(message.timestamp).toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (error) {
      return '';
    }
  }, [message.timestamp]);

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
        mb: 2,
        animation: isLast ? 'fadeIn 0.3s ease-in' : 'none',
        px: 1,
      }}
    >
      <Box
        sx={{
          maxWidth: { xs: '85%', sm: '70%' },
          minWidth: { xs: '150px', sm: '200px' },
          width: 'fit-content',
        }}
      >
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.5, sm: 2.5 },
            backgroundColor:
              message.role === 'user'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'rgba(255, 255, 255, 0.95)',
            color: '#000000 !important',
            borderRadius: message.role === 'user' ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
            backdropFilter: 'blur(10px)',
            border: message.role === 'user' ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
            boxShadow: message.role === 'user'
              ? '0 8px 32px rgba(102, 126, 234, 0.3)'
              : '0 4px 12px rgba(0, 0, 0, 0.08)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
            wordBreak: 'break-word',
            '&::before': {
              content: '""',
              position: 'absolute',
              bottom: 0,
              [message.role === 'user' ? 'right' : 'left']: '16px',
              width: 0,
              height: 0,
              border: '8px solid transparent',
              borderBottom: 0,
              borderTopColor: message.role === 'user' ? '#764ba2' : 'rgba(255, 255, 255, 0.95)',
              filter: message.role === 'user' ? 'none' : 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1))',
            },
            '&:hover': {
              transform: 'translateY(-2px) scale(1.02)',
              boxShadow: message.role === 'user'
                ? '0 12px 40px rgba(102, 126, 234, 0.4)'
                : '0 8px 25px rgba(0, 0, 0, 0.12)',
            },
            animation: isLast ? 'slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
            '@keyframes loading-blink': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.4 },
              '100%': { opacity: 1 },
            },
            ...(message.content === '応答を待っています...' && {
              animation: 'loading-blink 1.5s infinite ease-in-out',
            }),
            '@keyframes slideIn': {
              '0%': {
                opacity: 0,
                transform: `translateY(20px) ${message.role === 'user' ? 'translateX(20px)' : 'translateX(-20px)'}`,
              },
              '100%': {
                opacity: 1,
                transform: 'translateY(0) translateX(0)',
              },
            },
          }}
        >
          {/* メッセージコンテンツ */}
          <Typography
            variant="body1"
            component="div"
            sx={{
              lineHeight: 1.6,
              color: '#000000 !important',
              '& p': { 
                margin: 0,
                color: '#000000 !important'
              },
              '& *': {
                color: '#000000 !important'
              },
              '& code': {
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                padding: '0.2em 0.4em',
                borderRadius: '3px',
                fontSize: '0.9em',
                color: '#000000 !important'
              },
              '& pre': {
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
                padding: '1em',
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '0.9em',
                color: '#000000 !important'
              },
            }}
          >
            <MemoizedMarkdown content={message.content} />
          </Typography>

          {/* ソースドキュメント */}
          {message.sourceDocuments &&
            Array.isArray(message.sourceDocuments) &&
            message.sourceDocuments.length > 0 && (
              <SourceDocuments sourceDocuments={message.sourceDocuments} />
            )}
        </Paper>

        {/* タイムスタンプ */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: 'block',
            textAlign: message.role === 'user' ? 'right' : 'left',
            mt: 0.5,
            fontSize: '0.75rem',
            opacity: 0.8,
          }}
        >
          {formattedTime}
        </Typography>
      </Box>
    </Box>
  );
});

OptimizedChatMessage.displayName = 'OptimizedChatMessage';

export default OptimizedChatMessage;
