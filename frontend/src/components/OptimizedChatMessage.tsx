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
import { ChatMessageWithForm } from './ChatMessageWithForm';

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
  onSendMessage?: (message: string) => void;
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

const OptimizedChatMessage: React.FC<OptimizedChatMessageProps> = memo(({ message, isLast, onSendMessage }) => {
  const theme = useTheme();

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

  // アシスタントメッセージの場合、ChatMessageWithFormを使用
  if (message.role === 'assistant') {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-start',
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
          <ChatMessageWithForm
            content={message.content}
            role={message.role}
            onFlowExecuted={(result) => {
              if (result.type === 'send_message' && onSendMessage) {
                onSendMessage(result.message);
              }
            }}
          />
          
          {/* タイムスタンプ */}
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              textAlign: 'left',
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
  }

  // ユーザーメッセージは通常通り表示
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
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '20px 20px 6px 20px',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
            wordBreak: 'break-word',
            '&::before': {
              content: '""',
              position: 'absolute',
              bottom: 0,
              right: '16px',
              width: 0,
              height: 0,
              border: '8px solid transparent',
              borderBottom: 0,
              borderTopColor: '#764ba2',
            },
            '&:hover': {
              transform: 'translateY(-2px) scale(1.02)',
              boxShadow: '0 12px 40px rgba(102, 126, 234, 0.4)',
            },
            animation: isLast ? 'slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
            '@keyframes slideIn': {
              '0%': {
                opacity: 0,
                transform: 'translateY(20px) translateX(20px)',
              },
              '100%': {
                opacity: 1,
                transform: 'translateY(0) translateX(0)',
              },
            },
          }}
        >
          <Typography
            variant="body1"
            component="div"
            sx={{
              lineHeight: 1.6,
              '& p': { 
                margin: 0,
              },
            }}
          >
            <MemoizedMarkdown content={message.content} />
          </Typography>
        </Paper>

        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: 'block',
            textAlign: 'right',
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
