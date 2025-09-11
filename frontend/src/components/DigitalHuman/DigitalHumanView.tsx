import React, { useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
} from '@mui/icons-material';

interface DigitalHumanViewProps {
  isVisible?: boolean;
  isConnected?: boolean;
  isLoading?: boolean;
  error?: string | null;
  isFullscreen?: boolean;
  isMuted?: boolean;
  onToggleFullscreen?: () => void;
  onToggleMute?: () => void;
  stream?: MediaStream;
  videoRef?: React.RefObject<HTMLVideoElement>;
}

export const DigitalHumanView: React.FC<DigitalHumanViewProps> = ({
  isVisible = true,
  isConnected = false,
  isLoading = false,
  error = null,
  isFullscreen = false,
  isMuted = false,
  onToggleFullscreen,
  onToggleMute,
  stream,
  videoRef: externalVideoRef,
}) => {
  const theme = useTheme();
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const videoRef = externalVideoRef || internalVideoRef;

  // ストリームの設定
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream, videoRef]);

  if (!isVisible) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: isFullscreen ? '100vh' : '300px',
        borderRadius: isFullscreen ? 0 : 2,
        overflow: 'hidden',
        backgroundColor: 'grey.900',
        transition: 'all 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* 接続中のローディング表示 */}
      {isLoading && (
        <Box sx={{ textAlign: 'center', color: 'white' }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>
            接続中...
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            デジタルヒューマンに接続しています
          </Typography>
        </Box>
      )}

      {/* エラー表示 */}
      {error && !isLoading && (
        <Box sx={{ textAlign: 'center', color: 'white', p: 2 }}>
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 500, color: 'error.main' }}>
            接続エラー
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            {error}
          </Typography>
        </Box>
      )}

      {/* 接続済みの場合のビデオ表示 */}
      {isConnected && !isLoading && !error && (
        <>
          {/* ビデオ要素 */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted={isMuted}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />

          {/* オーバーレイコントロール */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
              opacity: 0,
              transition: 'opacity 0.2s ease',
              '&:hover': {
                opacity: 1,
              },
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              p: 2,
            }}
          >
            {/* 左上：タイトル */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="body2"
                sx={{
                  color: 'white',
                  fontWeight: 500,
                  textShadow: '0 2px 4px rgba(0,0,0,0.5)',
                }}
              >
                デジタルヒューマン
              </Typography>
            </Box>

            {/* 右上：コントロールボタン */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              {onToggleMute && (
                <IconButton
                  onClick={onToggleMute}
                  sx={{
                    width: 36,
                    height: 36,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    },
                  }}
                >
                  {isMuted ? (
                    <VolumeOffIcon sx={{ fontSize: '1.25rem' }} />
                  ) : (
                    <VolumeUpIcon sx={{ fontSize: '1.25rem' }} />
                  )}
                </IconButton>
              )}

              {onToggleFullscreen && (
                <IconButton
                  onClick={onToggleFullscreen}
                  sx={{
                    width: 36,
                    height: 36,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    },
                  }}
                >
                  {isFullscreen ? (
                    <FullscreenExitIcon sx={{ fontSize: '1.25rem' }} />
                  ) : (
                    <FullscreenIcon sx={{ fontSize: '1.25rem' }} />
                  )}
                </IconButton>
              )}
            </Box>
          </Box>
        </>
      )}

      {/* 未接続の場合のプレースホルダー */}
      {!isConnected && !isLoading && !error && (
        <Box sx={{ textAlign: 'center', color: 'white' }}>
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 500 }}>
            デジタルヒューマン
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            接続待機中...
          </Typography>
        </Box>
      )}
    </Box>
  );
};
