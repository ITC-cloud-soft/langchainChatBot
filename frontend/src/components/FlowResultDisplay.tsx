/**
 * Flow実行結果を美しく表示するコンポーネント
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
  Stack,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  AccessTime as AccessTimeIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

interface FlowStep {
  name: string;
  result: 'success' | 'error';
  data?: {
    WorkID?: number | string;
    FK_Node?: number | string;
    [key: string]: any;
  };
  messages?: string;
  msgcode?: string;
  ts?: string;
}

interface FlowResultData {
  [flowName: string]: FlowStep[];
}

interface FlowResultDisplayProps {
  flowId: string;
  success: boolean;
  resultData?: {
    message?: string;
    result_data?: FlowResultData;
    [key: string]: any;
  };
  error?: string;
}

export const FlowResultDisplay: React.FC<FlowResultDisplayProps> = ({
  flowId,
  success,
  resultData,
  error,
}) => {
  if (!success) {
    const result_data_err = resultData?.result_data || {};
    const errFlowNames = Object.keys(result_data_err);
    const errDisplayName = errFlowNames.length > 0 ? errFlowNames[0] : `Flow ${flowId}`;
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {errDisplayName} 実行失敗
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          {error || '不明なエラーが発生しました'}
        </Typography>
      </Alert>
    );
  }

  const result_data = resultData?.result_data || {};
  const flowNames = Object.keys(result_data);
  const displayName = flowNames.length > 0 ? flowNames[0] : `Flow ${flowId}`;

  if (flowNames.length === 0) {
    return (
      <Alert severity="success" sx={{ mt: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {displayName} 実行成功!
        </Typography>
      </Alert>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {displayName} 実行成功!
        </Typography>
      </Alert>

      {flowNames.map((flowName, index) => {
        const steps = result_data[flowName];
        if (!Array.isArray(steps)) return null;

        return (
          <Card key={index} sx={{ mb: 2, boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                📋 {flowName}
              </Typography>
              <Divider sx={{ my: 2 }} />

              <Stack spacing={2}>
                {steps.map((stepWrapper, stepIndex) => {
                  const stepName = Object.keys(stepWrapper)[0];
                  const stepData = (stepWrapper as any)[stepName] as FlowStep;
                  const isSuccess = stepData.result === 'success';

                  return (
                    <Card
                      key={stepIndex}
                      variant="outlined"
                      sx={{
                        borderLeft: 4,
                        borderLeftColor: isSuccess ? 'success.main' : 'error.main',
                        bgcolor: isSuccess ? 'success.lighter' : 'error.lighter',
                      }}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {isSuccess ? (
                            <CheckCircleIcon color="success" />
                          ) : (
                            <ErrorIcon color="error" />
                          )}
                          <Typography variant="subtitle1" fontWeight="bold">
                            ステップ {stepIndex + 1}: {stepName}
                          </Typography>
                          <Chip
                            label={isSuccess ? '成功' : '失敗'}
                            color={isSuccess ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>

                        {isSuccess && stepData.data && (
                          <Box sx={{ mt: 1 }}>
                            {stepData.data.WorkID && (
                              <Typography variant="body2" sx={{ mb: 0.5 }}>
                                • WorkID: <code style={{ 
                                  backgroundColor: '#f5f5f5', 
                                  padding: '2px 6px', 
                                  borderRadius: '4px',
                                  fontFamily: 'monospace'
                                }}>{stepData.data.WorkID}</code>
                              </Typography>
                            )}
                            {stepData.data.FK_Node && (
                              <Typography variant="body2">
                                • FK_Node: <code style={{ 
                                  backgroundColor: '#f5f5f5', 
                                  padding: '2px 6px', 
                                  borderRadius: '4px',
                                  fontFamily: 'monospace'
                                }}>{stepData.data.FK_Node}</code>
                              </Typography>
                            )}
                          </Box>
                        )}

                        {!isSuccess && (
                          <Box sx={{ mt: 1 }}>
                            {stepData.msgcode && (
                              <Typography variant="body2" color="error" sx={{ mb: 0.5 }}>
                                • エラーコード: <code style={{ 
                                  backgroundColor: '#ffebee', 
                                  padding: '2px 6px', 
                                  borderRadius: '4px',
                                  fontFamily: 'monospace'
                                }}>{stepData.msgcode}</code>
                              </Typography>
                            )}
                            {stepData.messages && (
                              <Typography variant="body2" color="error">
                                • エラーメッセージ: {stepData.messages}
                              </Typography>
                            )}
                          </Box>
                        )}

                        {stepData.ts && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}
                          >
                            <AccessTimeIcon sx={{ fontSize: 14 }} />
                            実行時刻: {new Date(stepData.ts).toLocaleString('ja-JP')}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </Stack>
            </CardContent>
          </Card>
        );
      })}

      {/* 詳細データの折りたたみ表示 */}
      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon />
            <Typography>📊 詳細データを表示</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box
            component="pre"
            sx={{
              backgroundColor: '#f5f5f5',
              p: 2,
              borderRadius: 1,
              overflow: 'auto',
              fontSize: '0.875rem',
              fontFamily: 'monospace',
            }}
          >
            {JSON.stringify(resultData, null, 2)}
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};
