import { createTheme, ThemeOptions } from '@mui/material/styles';

// カラーパレット定義
const colors = {
  primary: {
    main: '#667eea', // Modern indigo with blue tint
    light: '#818cf8', // Indigo-400
    dark: '#4c1d95', // Purple-900 for depth
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#f472b6', // Pink-400 for accent
    light: '#fb7185', // Rose-400
    dark: '#db2777', // Pink-600
    contrastText: '#ffffff',
  },
  success: {
    main: '#10b981', // Emerald-500
    light: '#34d399', // Emerald-400
    dark: '#059669', // Emerald-600
    contrastText: '#ffffff',
  },
  warning: {
    main: '#f59e0b', // Amber-500
    light: '#fbbf24', // Amber-400
    dark: '#d97706', // Amber-600
    contrastText: '#ffffff',
  },
  error: {
    main: '#ef4444', // Red-500
    light: '#f87171', // Red-400
    dark: '#dc2626', // Red-600
    contrastText: '#ffffff',
  },
  info: {
    main: '#3b82f6', // Blue-500
    light: '#60a5fa', // Blue-400
    dark: '#2563eb', // Blue-600
    contrastText: '#ffffff',
  },
  grey: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  background: {
    default: '#f8fafc',
    paper: '#ffffff',
    chat: '#f1f5f9',
    message: '#ffffff',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  text: {
    primary: '#111827',
    secondary: '#6b7280',
    disabled: '#d1d5db',
  },
};

// タイポグラフィ設定
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
  h1: {
    fontSize: '2.25rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.025em',
  },
  h2: {
    fontSize: '1.875rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.025em',
  },
  h3: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '-0.025em',
  },
  h4: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '-0.025em',
  },
  h5: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.5,
    letterSpacing: '-0.025em',
  },
  h6: {
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.5,
    letterSpacing: '-0.025em',
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.6,
    letterSpacing: '0em',
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.4,
    letterSpacing: '0.025em',
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.025em',
    textTransform: 'none' as const,
  },
};

// スペーシングシステム
const spacing = (factor: number) => `${0.25 * factor}rem`;

// ブレークポイント
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
        borderRadius: 12,
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
      },
      elevation1: {
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
      },
      elevation2: {
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      elevation3: {
        boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        fontWeight: 600,
        padding: '10px 20px',
        textTransform: 'none',
        fontSize: '0.9rem',
        letterSpacing: '0.025em',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&.MuiButton-contained': {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#ffffff',
          boxShadow: '0 4px 14px 0 rgba(102, 126, 234, 0.39)',
          '&:hover': {
            background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
            transform: 'translateY(-2px)',
            boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
          },
          '&:active': {
            transform: 'translateY(0px)',
          },
        },
        '&.MuiButton-outlined': {
          borderWidth: 2,
          borderColor: colors.primary.main,
          color: colors.primary.main,
          '&:hover': {
            borderColor: colors.primary.dark,
            color: colors.primary.dark,
            backgroundColor: `${colors.primary.main}08`,
            transform: 'translateY(-1px)',
          },
        },
        '&.MuiButton-text': {
          color: colors.primary.main,
          '&:hover': {
            backgroundColor: `${colors.primary.main}08`,
          },
        },
      },
      sizeSmall: {
        padding: '8px 16px',
        fontSize: '0.8125rem',
        borderRadius: 8,
      },
      sizeLarge: {
        padding: '14px 28px',
        fontSize: '0.9375rem',
        borderRadius: 14,
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 12,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '& fieldset': {
            borderColor: colors.grey[300],
            borderWidth: 2,
          },
          '&:hover fieldset': {
            borderColor: colors.primary.main,
          },
          '&.Mui-focused fieldset': {
            borderWidth: 2,
            borderColor: colors.primary.main,
            boxShadow: `0 0 0 4px ${colors.primary.main}20`,
          },
          '&.Mui-focused': {
            boxShadow: `0 0 0 4px ${colors.primary.main}20`,
          },
        },
        '& .MuiInputLabel-root': {
          color: colors.grey[500],
          '&.Mui-focused': {
            color: colors.primary.main,
            fontWeight: 600,
          },
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
        borderRadius: 12,
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
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
    '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    ...Array(19).fill('0 25px 50px -12px rgb(0 0 0 / 0.25)'),
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
