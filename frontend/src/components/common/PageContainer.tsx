import React from 'react';
import { Box, Container } from '@mui/material';

interface PageContainerProps {
  children: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  sx?: React.ComponentProps<typeof Box>['sx'];
}

const PageContainer: React.FC<PageContainerProps> = ({ children, maxWidth = 'lg', sx }) => {
  return (
    <Box
      sx={{
        flexGrow: 1,
        p: 3,
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        ...sx,
      }}
    >
      <Container maxWidth={maxWidth}>{children}</Container>
    </Box>
  );
};

export default PageContainer;
