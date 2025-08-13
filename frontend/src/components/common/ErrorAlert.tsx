import React from 'react';
import { Alert, AlertTitle, Box } from '@mui/material';

interface ErrorAlertProps {
  title?: string;
  message: string;
  severity?: 'error' | 'warning' | 'info' | 'success';
  onClose?: () => void;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'エラー',
  message,
  severity = 'error',
  onClose,
}) => {
  return (
    <Box mb={2}>
      <Alert severity={severity} onClose={onClose}>
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Box>
  );
};

export default ErrorAlert;
