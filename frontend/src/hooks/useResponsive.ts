import React, { useMemo, useCallback } from 'react';
import { useTheme, useMediaQuery } from '@mui/material';

interface UseResponsiveProps {
  breakpoint?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

interface ResponsiveValues {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  currentBreakpoint: string;
  spacing: (factor: number, factor2?: number) => string;
  fontSize: (size: 'small' | 'medium' | 'large') => string;
  padding: (size: 'small' | 'medium' | 'large') => number;
  borderRadius: (size: 'small' | 'medium' | 'large') => number;
}

export const useResponsive = ({ breakpoint = 'md' }: UseResponsiveProps = {}): ResponsiveValues => {
  const theme = useTheme();

  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));

  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isLargeDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const currentBreakpoint = useMemo(() => {
    if (isXs) return 'xs';
    if (isSm) return 'sm';
    if (isMd) return 'md';
    if (isLg) return 'lg';
    if (isXl) return 'xl';
    return 'unknown';
  }, [isXs, isSm, isMd, isLg, isXl]);

  // レスポンシブな間隔を計算
  const spacing = useCallback(
    (factor: number, factor2?: number) => {
      if (factor2 !== undefined) {
        return theme.spacing(factor, factor2);
      }
      return theme.spacing(factor);
    },
    [theme],
  );

  // レスポンシブなフォントサイズ
  const fontSize = useCallback(
    (size: 'small' | 'medium' | 'large') => {
      const sizes = {
        small: isMobile ? '0.875rem' : isTablet ? '0.9rem' : '1rem',
        medium: isMobile ? '1rem' : isTablet ? '1.1rem' : '1.25rem',
        large: isMobile ? '1.25rem' : isTablet ? '1.5rem' : '1.75rem',
      };
      return sizes[size];
    },
    [isMobile, isTablet],
  );

  // レスポンシブなパディング
  const padding = useCallback(
    (size: 'small' | 'medium' | 'large') => {
      const sizes = {
        small: isMobile ? 1 : isTablet ? 1.5 : 2,
        medium: isMobile ? 2 : isTablet ? 3 : 4,
        large: isMobile ? 3 : isTablet ? 4 : 6,
      };
      return sizes[size];
    },
    [isMobile, isTablet],
  );

  // レスポンシブなボーダー半径
  const borderRadius = useCallback(
    (size: 'small' | 'medium' | 'large') => {
      const sizes = {
        small: isMobile ? 4 : isTablet ? 6 : 8,
        medium: isMobile ? 8 : isTablet ? 12 : 16,
        large: isMobile ? 12 : isTablet ? 16 : 24,
      };
      return sizes[size];
    },
    [isMobile, isTablet],
  );

  return {
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    currentBreakpoint,
    spacing,
    fontSize,
    padding,
    borderRadius,
  };
};

// レスポンシブなスタイルを生成するヘルパー関数
export const createResponsiveStyles = (responsive: ResponsiveValues) => {
  const { isMobile, isTablet, isDesktop, spacing, fontSize, padding, borderRadius } = responsive;

  return {
    // コンテナスタイル
    container: {
      padding: padding('medium'),
      maxWidth: isMobile ? '100%' : isTablet ? '90%' : '80%',
      margin: '0 auto',
    },

    // ヘッダースタイル
    header: {
      padding: padding('small'),
      marginBottom: spacing(2),
      fontSize: fontSize('medium'),
    },

    // ボタンスタイル
    button: {
      padding: isMobile ? spacing(1, 2) : spacing(1.5, 3),
      fontSize: fontSize('small'),
      borderRadius: borderRadius('small'),
    },

    // 入力フィールドスタイル
    input: {
      padding: spacing(1),
      fontSize: fontSize('small'),
      borderRadius: borderRadius('small'),
    },

    // カードスタイル
    card: {
      padding: padding('medium'),
      borderRadius: borderRadius('medium'),
      marginBottom: spacing(2),
    },

    // リストアイテムスタイル
    listItem: {
      padding: spacing(1.5),
      borderRadius: borderRadius('small'),
      marginBottom: spacing(1),
    },

    // タイポグラフィスタイル
    typography: {
      h1: { fontSize: fontSize('large'), fontWeight: 'bold' },
      h2: { fontSize: isMobile ? '1.5rem' : '1.75rem', fontWeight: 'bold' },
      h3: { fontSize: isMobile ? '1.25rem' : '1.5rem', fontWeight: 'bold' },
      body1: { fontSize: fontSize('small') },
      body2: { fontSize: isMobile ? '0.8rem' : '0.875rem' },
      caption: { fontSize: isMobile ? '0.7rem' : '0.75rem' },
    },
  };
};

// レスポンシブなレイアウトフック
export const useResponsiveLayout = () => {
  const responsive = useResponsive();

  const getLayoutConfig = useCallback(() => {
    const { isMobile, isTablet } = responsive;

    return {
      // ナビゲーション設定
      navigation: {
        drawerWidth: isMobile ? 280 : isTablet ? 320 : 360,
        permanent: !isMobile,
        variant: isMobile ? ('temporary' as const) : ('permanent' as const),
      },

      // コンテンツ設定
      content: {
        maxWidth: isMobile ? '100%' : isTablet ? '90%' : '1200px',
        padding: isMobile ? 16 : isTablet ? 24 : 32,
        gap: isMobile ? 16 : isTablet ? 24 : 32,
      },

      // グリッド設定
      grid: {
        columns: isMobile ? 1 : isTablet ? 2 : 3,
        spacing: isMobile ? 2 : isTablet ? 3 : 4,
      },

      // フォーム設定
      form: {
        inputSize: isMobile ? ('small' as const) : ('medium' as const),
        buttonSize: isMobile ? ('small' as const) : ('medium' as const),
        labelPosition: isMobile ? ('top' as const) : ('left' as const),
      },

      // ダイアログ設定
      dialog: {
        maxWidth: isMobile ? ('sm' as const) : isTablet ? ('md' as const) : ('lg' as const),
        fullWidth: true,
        fullScreen: isMobile,
      },
    };
  }, [responsive]);

  return {
    responsive,
    layout: getLayoutConfig(),
  };
};
