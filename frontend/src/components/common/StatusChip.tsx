import React from 'react';
import { Chip, ChipProps } from '@mui/material';

interface StatusChipProps {
  status: string;
  label?: string;
  variant?: 'filled' | 'outlined';
  size?: 'small' | 'medium';
  color?: ChipProps['color'];
  customColors?: Record<string, string>;
}

const StatusChip: React.FC<StatusChipProps> = ({
  status,
  label,
  variant = 'filled',
  size = 'small',
  color,
  customColors = {},
}) => {
  const getStatusColor = (statusValue: string): ChipProps['color'] => {
    const colorMap: Record<string, ChipProps['color']> = {
      active: 'success',
      completed: 'success',
      success: 'success',
      online: 'success',
      enabled: 'success',

      pending: 'warning',
      processing: 'warning',
      waiting: 'warning',
      warning: 'warning',

      error: 'error',
      failed: 'error',
      offline: 'error',
      disabled: 'error',
      inactive: 'error',

      info: 'info',
      running: 'info',
      started: 'info',

      default: 'default',
      unknown: 'default',
    };

    return color ?? colorMap[statusValue.toLowerCase()] ?? 'default';
  };

  const getCustomColor = (statusValue: string): string | undefined => {
    return customColors[statusValue.toLowerCase()];
  };

  const getStatusLabel = (statusValue: string): string => {
    const labelMap: Record<string, string> = {
      active: '有効',
      inactive: '無効',
      pending: '保留中',
      processing: '処理中',
      completed: '完了',
      success: '成功',
      error: 'エラー',
      failed: '失敗',
      online: 'オンライン',
      offline: 'オフライン',
      enabled: '有効',
      disabled: '無効',
      running: '実行中',
      stopped: '停止',
      waiting: '待機中',
    };

    return label ?? labelMap[statusValue.toLowerCase()] ?? statusValue;
  };

  const chipColor = getStatusColor(status);
  const customColor = getCustomColor(status);
  const displayLabel = getStatusLabel(status);

  // コンポーネントを小さな関数に分割して行数を減らす
  const StatusChipInner = () => (
    <Chip
      label={displayLabel}
      variant={variant}
      size={size}
      color={chipColor}
      sx={
        customColor
          ? {
              backgroundColor: variant === 'filled' ? customColor : undefined,
              borderColor: variant === 'outlined' ? customColor : undefined,
              color: variant === 'filled' ? 'white' : customColor,
            }
          : undefined
      }
    />
  );

  return <StatusChipInner />;
};

export default StatusChip;
