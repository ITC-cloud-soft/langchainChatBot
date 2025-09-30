import React, { memo, useCallback, useRef, useEffect, useState } from 'react';
import { FixedSizeList as List } from 'react-window';
import { Box, SxProps } from '@mui/material';
import OptimizedChatMessage from './OptimizedChatMessage';

interface VirtualizedMessageListProps {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    sourceDocuments?: Array<{
      content: string;
      metadata: Record<string, unknown>;
    }>;
  }>;
  itemSize: number;
  height?: number;
  width?: number | string;
  sx?: SxProps;
}

interface RowData {
  index: number;
  style: React.CSSProperties;
  data: {
    messages: VirtualizedMessageListProps['messages'];
  };
}

const MessageRow: React.FC<RowData> = memo(({ index, style, data }) => {
  const { messages } = data;
  const message = messages[index];

  if (!message) {
    return null;
  }

  return (
    <div style={style}>
      <OptimizedChatMessage message={message} isLast={index === messages.length - 1} />
    </div>
  );
});

MessageRow.displayName = 'MessageRow';

const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  messages,
  itemSize,
  height,
  width,
  sx,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    if (!height || !width) {
      const updateDimensions = () => {
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          setDimensions({
            width: rect.width || 800,
            height: rect.height || 600,
          });
        }
      };

      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, [height, width]);

  const itemData = React.useMemo(() => ({ messages }), [messages]);

  const getItemKey = useCallback(
    (index: number) => {
      const message = messages[index];
      return `${message.timestamp}-${message.role}-${index}`;
    },
    [messages],
  );

  const actualHeight = height || dimensions.height;
  const actualWidth = width || dimensions.width;

  if (messages.length === 0) {
    return (
      <Box
        ref={containerRef}
        sx={{
          height: '100%',
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          ...sx,
        }}
      >
        メッセージがありません
      </Box>
    );
  }

  return (
    <Box ref={containerRef} sx={{ height: '100%', width: '100%', ...sx }}>
      <List
        height={actualHeight}
        width={actualWidth}
        itemSize={itemSize}
        itemCount={messages.length}
        itemData={itemData}
        itemKey={getItemKey}
        overscanCount={5}
      >
        {MessageRow}
      </List>
    </Box>
  );
};

export default VirtualizedMessageList;
