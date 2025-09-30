import { createTheme, ThemeOptions } from '@mui/material/styles';

// カラーパレット定義（現代的なAIチャットアプリ風）
const colors = {
  primary: {
    main: '#0ea5e9', // Sky blue - より鮮やかでモダンな青
    light: '#38bdf8', // Sky-400
    dark: '#0284c7', // Sky-600 for depth
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#8b5cf6', // Violet - より洗練された紫
    light: '#a78bfa', // Violet-400
    dark: '#7c3aed', // Violet-600
    contrastText: '#ffffff',
  },
  success: {
    main: '#06d6a0', // Emerald - より鮮やかな緑
    light: '#34d399', // Emerald-400
    dark: '#059669', // Emerald-600
    contrastText: '#ffffff',
  },
  warning: {
    main: '#f59e0b', // Amber - 維持
    light: '#fbbf24', // Amber-400
    dark: '#d97706', // Amber-600
    contrastText: '#ffffff',
  },
  error: {
    main: '#ef4444', // Red - 維持
    light: '#f87171', // Red-400
    dark: '#dc2626', // Red-600
    contrastText: '#ffffff',
  },
  info: {
    main: '#06b6d4', // Cyan - よりクリーンな青
    light: '#22d3ee', // Cyan-400
    dark: '#0891b2', // Cyan-600
    contrastText: '#ffffff',
  },
  grey: {
    50: '#fafafa',
    100: '#f4f4f5',
    200: '#e4e4e7',
    300: '#d4d4d8',
    400: '#a1a1aa',
    500: '#71717a',
    600: '#52525b',
    700: '#3f3f46',
    800: '#27272a',
    900: '#18181b',
  },
  background: {
    default: '#fafafa', // より明るい背景
    paper: '#ffffff',
    chat: '#f8fafc', // よりクリーンなチャット背景
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%)', // メインカラーを使ったグレーデーション
    message: '#ffffff',
  },
  text: {
    primary: '#18181b', // より濃い黒
    secondary: '#71717a', // より濃いグレー
    disabled: '#d4d4d8',
  },
};

// タイポグラフィ設定（改善版）
const typography = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  fontWeightLight: 300,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightBold: 600,
  fontWeightExtraBold: 700,
  h1: {
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.1,
    letterSpacing: '-0.025em',
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.2,
    letterSpacing: '-0.025em',
  },
  h3: {
    fontSize: '1.75rem',
    fontWeight: 600,
    lineHeight: 1.25,
    letterSpacing: '-0.025em',
  },
  h4: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.025em',
  },
  h5: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.35,
    letterSpacing: '-0.025em',
  },
  h6: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '-0.025em',
  },
  subtitle1: {
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0em',
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.01em',
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.7,
    letterSpacing: '0.01em',
    fontWeight: 400,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.6,
    letterSpacing: '0.01em',
    fontWeight: 400,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
    letterSpacing: '0.025em',
    fontWeight: 400,
  },
  overline: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
    letterSpacing: '0.08em',
    fontWeight: 500,
    textTransform: 'uppercase' as const,
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.02em',
    textTransform: 'none' as const,
  },
};

// スペーシングシステム
const spacing = (factor: number) => `${0.25 * factor}rem`;

// ブレークポイント（改善版）
const breakpoints = {
  values: {
    xs: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    xxl: 1536,
  },
};

// コンポーネント固有のスタイルオーバーライド
const components: ThemeOptions['components'] = {
  MuiCssBaseline: {
    styleOverrides: {
      '*': {
        boxSizing: 'border-box',
      },
      html: {
        WebkitFontSmoothing: 'antialiased',
        MozOsxFontSmoothing: 'grayscale',
        scrollBehavior: 'smooth',
      },
      body: {
        fontFamily: typography.fontFamily,
        backgroundColor: colors.background.default,
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        borderRadius: 16,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      },
      elevation0: {
        boxShadow: 'none',
      },
      elevation1: {
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.08)',
      },
      elevation2: {
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.1)',
      },
      elevation3: {
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.12)',
      },
      elevation4: {
        boxShadow: '0 12px 32px rgba(0, 0, 0, 0.1), 0 6px 16px rgba(0, 0, 0, 0.14)',
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        fontWeight: 600,
        padding: '12px 24px',
        textTransform: 'none',
        fontSize: '0.9rem',
        letterSpacing: '0.02em',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
          transition: 'left 0.5s',
        },
        '&.MuiButton-contained': {
          background: 'linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%)',
          color: '#ffffff',
          boxShadow: '0 4px 20px rgba(14, 165, 233, 0.25)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          '&:hover': {
            background: 'linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)',
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 30px rgba(14, 165, 233, 0.35)',
            '&::before': {
              left: '100%',
            },
          },
          '&:active': {
            transform: 'translateY(0px)',
            boxShadow: '0 2px 10px rgba(14, 165, 233, 0.2)',
          },
        },
        '&.MuiButton-outlined': {
          borderWidth: 2,
          borderColor: colors.primary.main,
          color: colors.primary.main,
          backgroundColor: 'rgba(14, 165, 233, 0.05)',
          backdropFilter: 'blur(10px)',
          '&:hover': {
            borderColor: colors.primary.dark,
            color: colors.primary.dark,
            backgroundColor: 'rgba(14, 165, 233, 0.1)',
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 15px rgba(14, 165, 233, 0.15)',
          },
        },
        '&.MuiButton-text': {
          color: colors.primary.main,
          '&:hover': {
            backgroundColor: 'rgba(14, 165, 233, 0.08)',
            transform: 'translateY(-1px)',
          },
        },
        '&:disabled': {
          opacity: 0.6,
          transform: 'none !important',
          '&:hover': {
            transform: 'none !important',
          },
        },
      },
      sizeSmall: {
        padding: '8px 16px',
        fontSize: '0.8125rem',
        borderRadius: 8,
        minHeight: 36,
      },
      sizeLarge: {
        padding: '16px 32px',
        fontSize: '1rem',
        borderRadius: 16,
        minHeight: 56,
      },
      containedPrimary: {
        '&:hover': {
          background: 'linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)',
        },
      },
      containedSecondary: {
        background: 'linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%)',
        '&:hover': {
          background: 'linear-gradient(135deg, #7c3aed 0%, #0891b2 100%)',
        },
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 16,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
          '& fieldset': {
            borderColor: 'rgba(255, 255, 255, 0.3)',
            borderWidth: 1,
          },
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            '& fieldset': {
              borderColor: colors.primary.light,
              borderWidth: 1,
            },
          },
          '&.Mui-focused': {
            backgroundColor: '#ffffff',
            boxShadow: `0 0 0 3px rgba(14, 165, 233, 0.1), 0 8px 25px rgba(0, 0, 0, 0.1)`,
            border: `1px solid ${colors.primary.main}`,
            '& fieldset': {
              borderWidth: 1,
              borderColor: colors.primary.main,
            },
          },
          '&.Mui-disabled': {
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            '& fieldset': {
              borderColor: colors.grey[300],
            },
          },
        },
        '& .MuiInputLabel-root': {
          color: colors.grey[600],
          fontWeight: 500,
          '&.Mui-focused': {
            color: colors.primary.main,
            fontWeight: 600,
          },
          '&.Mui-disabled': {
            color: colors.grey[400],
          },
        },
        '& .MuiOutlinedInput-input': {
          fontSize: '0.95rem',
          lineHeight: 1.5,
          padding: '16px 20px',
          '&::placeholder': {
            color: colors.grey[500],
            opacity: 0.8,
            fontWeight: 400,
          },
        },
        '& .MuiOutlinedInput-multiline': {
          padding: '16px 20px',
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        fontWeight: 500,
      },
    },
  },
  MuiAvatar: {
    styleOverrides: {
      root: {
        borderRadius: 8,
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05), 0 2px 8px rgba(0, 0, 0, 0.08)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.12)',
          transform: 'translateY(-2px)',
        },
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRadius: '0 12px 12px 0',
      },
    },
  },
  MuiListItem: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        marginBottom: 2,
        '&:hover': {
          backgroundColor: `${colors.primary.main}08`,
        },
      },
    },
  },
};

// ライトテーマ設定
const lightTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    grey: colors.grey,
    background: {
      default: colors.background.default,
      paper: colors.background.paper,
    },
    text: colors.text,
  },
  typography,
  spacing,
  breakpoints,
  components,
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0 1px 2px 0 rgba(0, 0, 0, 0.04), 0 1px 1px 0 rgba(0, 0, 0, 0.06)',
    '0 2px 4px 0 rgba(0, 0, 0, 0.04), 0 2px 2px 0 rgba(0, 0, 0, 0.06)',
    '0 4px 8px 0 rgba(0, 0, 0, 0.04), 0 4px 4px 0 rgba(0, 0, 0, 0.06)',
    '0 6px 12px 0 rgba(0, 0, 0, 0.04), 0 6px 6px 0 rgba(0, 0, 0, 0.06)',
    '0 8px 16px 0 rgba(0, 0, 0, 0.04), 0 8px 8px 0 rgba(0, 0, 0, 0.06)',
    '0 12px 24px 0 rgba(0, 0, 0, 0.04), 0 12px 12px 0 rgba(0, 0, 0, 0.06)',
    '0 16px 32px 0 rgba(0, 0, 0, 0.04), 0 16px 16px 0 rgba(0, 0, 0, 0.06)',
    '0 20px 40px 0 rgba(0, 0, 0, 0.04), 0 20px 20px 0 rgba(0, 0, 0, 0.06)',
    '0 24px 48px 0 rgba(0, 0, 0, 0.04), 0 24px 24px 0 rgba(0, 0, 0, 0.06)',
    '0 28px 56px 0 rgba(0, 0, 0, 0.04), 0 28px 28px 0 rgba(0, 0, 0, 0.06)',
    '0 32px 64px 0 rgba(0, 0, 0, 0.04), 0 32px 32px 0 rgba(0, 0, 0, 0.06)',
    '0 36px 72px 0 rgba(0, 0, 0, 0.04), 0 36px 36px 0 rgba(0, 0, 0, 0.06)',
    '0 40px 80px 0 rgba(0, 0, 0, 0.04), 0 40px 40px 0 rgba(0, 0, 0, 0.06)',
    '0 44px 88px 0 rgba(0, 0, 0, 0.04), 0 44px 44px 0 rgba(0, 0, 0, 0.06)',
    '0 48px 96px 0 rgba(0, 0, 0, 0.04), 0 48px 48px 0 rgba(0, 0, 0, 0.06)',
    '0 52px 104px 0 rgba(0, 0, 0, 0.04), 0 52px 52px 0 rgba(0, 0, 0, 0.06)',
    '0 56px 112px 0 rgba(0, 0, 0, 0.04), 0 56px 56px 0 rgba(0, 0, 0, 0.06)',
    '0 60px 120px 0 rgba(0, 0, 0, 0.04), 0 60px 60px 0 rgba(0, 0, 0, 0.06)',
    '0 64px 128px 0 rgba(0, 0, 0, 0.04), 0 64px 64px 0 rgba(0, 0, 0, 0.06)',
    '0 68px 136px 0 rgba(0, 0, 0, 0.04), 0 68px 68px 0 rgba(0, 0, 0, 0.06)',
    '0 72px 144px 0 rgba(0, 0, 0, 0.04), 0 72px 72px 0 rgba(0, 0, 0, 0.06)',
    '0 76px 152px 0 rgba(0, 0, 0, 0.04), 0 76px 76px 0 rgba(0, 0, 0, 0.06)',
    '0 80px 160px 0 rgba(0, 0, 0, 0.04), 0 80px 80px 0 rgba(0, 0, 0, 0.06)',
  ] as any,
};

// ダークテーマ設定
const darkTheme: ThemeOptions = {
  ...lightTheme,
  palette: {
    mode: 'dark',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    grey: colors.grey,
    background: {
      default: '#111827',
      paper: '#1f2937',
    },
    text: {
      primary: '#f9fafb',
      secondary: '#d1d5db',
      disabled: '#6b7280',
    },
  },
};

// テーマ作成関数
export const createAppTheme = (mode: 'light' | 'dark' = 'light') => {
  const themeOptions = mode === 'dark' ? darkTheme : lightTheme;
  return createTheme(themeOptions);
};

export default createAppTheme;
