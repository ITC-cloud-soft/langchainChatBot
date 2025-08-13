/**
 * 共通ユーティリティ関数
 */

// エラーハンドリング用の型定義
interface ApiError {
  response?: {
    data?: {
      message?: string;
      error?: string;
    };
  };
  message?: string;
}

/**
 * 日付をフォーマットする
 * @param dateString 日付文字列
 * @returns フォーマットされた日付文字列
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);

  // 無効な日付の場合は元の文字列を返す
  if (isNaN(date.getTime())) {
    return dateString;
  }

  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * 時刻をフォーマットする
 * @param dateString 日付文字列
 * @returns フォーマットされた時刻文字列
 */
export const formatTime = (dateString: string): string => {
  const date = new Date(dateString);

  // 無効な日付の場合はエラーメッセージを返す
  if (isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  return date.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * テキストを指定された長さに切り詰める
 * @param text テキスト
 * @param maxLength 最大長
 * @param ellipsis 省略記号（デフォルト: '...'）
 * @returns 切り詰められたテキスト
 */
export const truncateText = (text: string, maxLength = 100, ellipsis = '...'): string => {
  if (text.length <= maxLength) return text;
  const truncatedLength = maxLength - ellipsis.length;
  return text.substring(0, truncatedLength) + ellipsis;
};

/**
 * オブジェクトをクエリパラメータ文字列に変換する
 * @param params オブジェクト
 * @returns クエリパラメータ文字列
 */
export const objectToQueryString = (params: Record<string, string | number | boolean>): string => {
  return Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
};

/**
 * ファイルサイズを人間が読める形式に変換する
 * @param bytes バイト数
 * @returns フォーマットされたファイルサイズ
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * エラーメッセージを取得する
 * @param error エラーオブジェクト
 * @returns エラーメッセージ
 */
export const getErrorMessage = (error: ApiError | string | unknown): string => {
  if (!error) return '不明なエラーが発生しました';

  if (typeof error === 'string') return error;

  // unknown型をApiErrorにキャスト
  const apiError = error as ApiError;

  if (apiError.response) {
    // APIからのエラーレスポンス
    return (
      apiError.response.data?.message ?? apiError.response.data?.error ?? 'APIエラーが発生しました'
    );
  }

  if (apiError.message) return apiError.message;

  return '不明なエラーが発生しました';
};

/**
 * メタデータオブジェクトをフォーマットされた文字列に変換する
 * @param metadata メタデータオブジェクト
 * @returns フォーマットされた文字列
 */
export const formatMetadata = (metadata: Record<string, unknown>): string => {
  return JSON.stringify(metadata, null, 2);
};

/**
 * UUIDを生成する
 * @returns UUID文字列
 */
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

/**
 * セッションIDを生成する
 * @returns セッションID
 */
export const generateSessionId = (): string => {
  return `session_${Date.now()}`;
};

/**
 * データをローカルストレージに保存する
 * @param key キー
 * @param data データ
 */
export const saveToLocalStorage = (key: string, data: unknown): void => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error(`Failed to save data to localStorage: ${error}`);
  }
};

/**
 * ローカルストレージからデータを取得する
 * @param key キー
 * @param defaultValue デフォルト値
 * @returns 保存されたデータまたはデフォルト値
 */
export const getFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Failed to get data from localStorage: ${error}`);
    return defaultValue;
  }
};

/**
 * ローカルストレージからデータを削除する
 * @param key キー
 */
export const removeFromLocalStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Failed to remove data from localStorage: ${error}`);
  }
};

/**
 * 配列を指定されたサイズのチャンクに分割する
 * @param array 配列
 * @param chunkSize チャンクサイズ
 * @returns チャンクの配列
 */
export const chunkArray = <T>(array: T[], chunkSize: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
};

/**
 * オブジェクトを深くコピーする
 * @param obj オブジェクト
 * @returns コピーされたオブジェクト
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;

  const clonedObj = {} as T;
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      clonedObj[key] = deepClone(obj[key]);
    }
  }
  return clonedObj;
};

/**
 * デバウンス関数を作成する
 * @param func デバウンスする関数
 * @param delay 遅延時間（ミリ秒）
 * @returns デバウンスされた関数
 */
export const debounce = <T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number,
): ((...args: Parameters<T>) => void) & { cancel: () => void } => {
  let timeoutId: ReturnType<typeof setTimeout>;

  const debounced = ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as ((...args: Parameters<T>) => void) & { cancel: () => void };

  // キャンセルメソッドを追加
  debounced.cancel = () => {
    clearTimeout(timeoutId);
  };

  return debounced;
};

/**
 * スロットル関数を作成する
 * @param func スロットルする関数
 * @param delay 遅延時間（ミリ秒）
 * @returns スロットルされた関数
 */
export const throttle = <T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number,
): ((...args: Parameters<T>) => void) & { cancel: () => void } => {
  let lastCall = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const throttled = ((...args: Parameters<T>) => {
    const now = Date.now();

    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    } else if (!timeoutId) {
      timeoutId = setTimeout(
        () => {
          lastCall = Date.now();
          func(...args);
          timeoutId = null;
        },
        delay - (now - lastCall),
      );
    }
  }) as ((...args: Parameters<T>) => void) & { cancel: () => void };

  // キャンセルメソッドを追加
  throttled.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return throttled;
};
