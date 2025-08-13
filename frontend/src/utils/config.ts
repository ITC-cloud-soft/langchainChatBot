/**
 * 設定管理に関するユーティリティ関数
 */

import * as toml from '@iarna/toml';
import type { JsonMap } from '@iarna/toml';

// 検証スキーマの型定義
interface ValidationSchema {
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  enum?: unknown[];
  properties?: Record<string, ValidationSchema>;
}

interface ConfigSection {
  [key: string]: unknown;
}

/**
 * TOML形式の設定を解析する
 * @param tomlString TOML形式の文字列
 * @returns 解析された設定オブジェクト
 */
export const parseTOML = (tomlString: string): Record<string, unknown> => {
  try {
    const parsed = toml.parse(tomlString) as JsonMap;
    return parsed as Record<string, unknown>;
  } catch (error) {
    console.error('Error parsing TOML:', error);
    throw new Error('TOMLの解析に失敗しました');
  }
};

/**
 * 設定オブジェクトをTOML形式の文字列に変換する
 * @param config 設定オブジェクト
 * @returns TOML形式の文字列
 */
export const stringifyToTOML = (config: Record<string, unknown>): string => {
  try {
    return toml.stringify(config as JsonMap);
  } catch (error) {
    console.error('Error stringifying to TOML:', error);
    throw new Error('TOMLへの変換に失敗しました');
  }
};

/**
 * 設定オブジェクトを検証する
 * @param config 設定オブジェクト
 * @param schema 検証スキーマ
 * @returns 検証結果
 */
export const validateConfig = (
  config: Record<string, unknown>,
  schema: Record<string, ValidationSchema>,
): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  // 簡易的な検証ロジック
  // 実際の実装では、より高度な検証ライブラリを使用することをお勧めします

  const validateSection = (
    section: ConfigSection,
    sectionSchema: Record<string, ValidationSchema>,
    path: string,
  ) => {
    for (const key in sectionSchema) {
      const fullPath = path ? `${path}.${key}` : key;
      const expectedType = sectionSchema[key];
      const actualValue = section[key];

      if (actualValue === undefined) {
        // 必須フィールドのチェック
        if (expectedType.required) {
          errors.push(`${fullPath} は必須です`);
        }
        continue;
      }

      // 型のチェック
      if (expectedType.type && typeof actualValue !== expectedType.type) {
        errors.push(`${fullPath} は ${expectedType.type} 型である必要があります`);
      }

      // 値の範囲チェック
      if (expectedType.min !== undefined && Number(actualValue) < expectedType.min) {
        errors.push(`${fullPath} は ${expectedType.min} 以上である必要があります`);
      }

      if (expectedType.max !== undefined && Number(actualValue) > expectedType.max) {
        errors.push(`${fullPath} は ${expectedType.max} 以下である必要があります`);
      }

      // 配列の長さチェック
      if (
        expectedType.minLength !== undefined &&
        Array.isArray(actualValue) &&
        actualValue.length < expectedType.minLength
      ) {
        errors.push(`${fullPath} は少なくとも ${expectedType.minLength} 要素が必要です`);
      }

      if (
        expectedType.maxLength !== undefined &&
        Array.isArray(actualValue) &&
        actualValue.length > expectedType.maxLength
      ) {
        errors.push(`${fullPath} は最大 ${expectedType.maxLength} 要素までです`);
      }

      // 文字列の長さチェック
      if (
        expectedType.minLength !== undefined &&
        typeof actualValue === 'string' &&
        actualValue.length < expectedType.minLength
      ) {
        errors.push(`${fullPath} は少なくとも ${expectedType.minLength} 文字が必要です`);
      }

      if (
        expectedType.maxLength !== undefined &&
        typeof actualValue === 'string' &&
        actualValue.length > expectedType.maxLength
      ) {
        errors.push(`${fullPath} は最大 ${expectedType.maxLength} 文字までです`);
      }

      // パターンチェック
      if (
        expectedType.pattern &&
        typeof actualValue === 'string' &&
        !new RegExp(expectedType.pattern).test(actualValue)
      ) {
        errors.push(`${fullPath} はパターン ${expectedType.pattern} に一致する必要があります`);
      }

      // 列挙値チェック
      if (expectedType.enum && !expectedType.enum.includes(actualValue)) {
        errors.push(`${fullPath} は有効な値ではありません`);
      }

      // ネストされたオブジェクトの検証
      if (expectedType.properties && typeof actualValue === 'object' && actualValue !== null) {
        validateSection(actualValue as ConfigSection, expectedType.properties, fullPath);
      }
    }
  };

  validateSection(config as ConfigSection, schema, '');

  return {
    valid: errors.length === 0,
    errors,
  };
};

/**
 * 設定オブジェクトをマージする
 * @param base ベース設定
 * @param override 上書き設定
 * @returns マージされた設定
 */
export const mergeConfigs = (
  base: Record<string, unknown>,
  override: Record<string, unknown>,
): Record<string, unknown> => {
  const result = { ...base };

  for (const key in override) {
    const baseValue = result[key];
    const overrideValue = override[key];

    if (
      typeof baseValue === 'object' &&
      baseValue !== null &&
      typeof overrideValue === 'object' &&
      overrideValue !== null &&
      !Array.isArray(baseValue) &&
      !Array.isArray(overrideValue)
    ) {
      result[key] = mergeConfigs(
        baseValue as Record<string, unknown>,
        overrideValue as Record<string, unknown>,
      );
    } else {
      result[key] = overrideValue;
    }
  }

  return result;
};

/**
 * 設定オブジェクトからデフォルト値を設定する
 * @param config 設定オブジェクト
 * @param defaults デフォルト値
 * @returns デフォルト値が設定された設定
 */
export const applyDefaults = (
  config: Record<string, unknown>,
  defaults: Record<string, unknown>,
): Record<string, unknown> => {
  const result = { ...config };

  for (const key in defaults) {
    if (result[key] === undefined) {
      result[key] = defaults[key];
    } else if (
      typeof result[key] === 'object' &&
      result[key] !== null &&
      typeof defaults[key] === 'object' &&
      defaults[key] !== null &&
      !Array.isArray(result[key]) &&
      !Array.isArray(defaults[key])
    ) {
      result[key] = applyDefaults(
        result[key] as Record<string, unknown>,
        defaults[key] as Record<string, unknown>,
      );
    }
  }

  return result;
};

/**
 * 設定オブジェクトをクリーンアップする（undefined値を削除）
 * @param config 設定オブジェクト
 * @returns クリーンアップされた設定
 */
export const cleanConfig = (config: Record<string, unknown>): Record<string, unknown> => {
  const result: Record<string, unknown> = {};

  for (const key in config) {
    const value = config[key];
    if (value !== undefined) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        const cleaned = cleanConfig(value as Record<string, unknown>);
        if (Object.keys(cleaned).length > 0) {
          result[key] = cleaned;
        }
      } else {
        result[key] = value;
      }
    }
  }

  return result;
};

/**
 * 設定変更を記録する
 * @param oldConfig 古い設定
 * @param newConfig 新しい設定
 * @param path 現在のパス
 * @returns 変更のリスト
 */
export const recordChange = (
  oldConfig: Record<string, unknown>,
  newConfig: Record<string, unknown>,
  path: string = '',
): string[] => {
  const changes: string[] = [];
  const allKeys = new Set([...Object.keys(oldConfig), ...Object.keys(newConfig)]);

  for (const key of allKeys) {
    const fullPath = path ? `${path}.${key}` : key;
    const oldValue = oldConfig[key];
    const newValue = newConfig[key];

    if (oldValue === undefined) {
      changes.push(`追加: ${fullPath} = ${JSON.stringify(newValue)}`);
    } else if (newValue === undefined) {
      changes.push(`削除: ${fullPath}`);
    } else if (
      typeof oldValue === 'object' &&
      oldValue !== null &&
      typeof newValue === 'object' &&
      newValue !== null &&
      !Array.isArray(oldValue) &&
      !Array.isArray(newValue)
    ) {
      const nestedChanges = recordChange(
        oldValue as Record<string, unknown>,
        newValue as Record<string, unknown>,
        fullPath,
      );
      changes.push(...nestedChanges);
    } else if (oldValue !== newValue) {
      changes.push(
        `変更: ${fullPath} = ${JSON.stringify(newValue)} (以前: ${JSON.stringify(oldValue)})`,
      );
    }
  }

  return changes;
};

/**
 * 環境変数から設定を読み込む
 * @param prefix 環境変数のプレフィックス
 * @returns 設定オブジェクト
 */
export const loadConfigFromEnv = (prefix: string = 'VITE_'): Record<string, unknown> => {
  const config: Record<string, unknown> = {};

  // Viteではimport.meta.envから環境変数にアクセス
  const envVars = import.meta.env as Record<string, string>;

  for (const key in envVars) {
    if (key.startsWith(prefix)) {
      const configKey = key.slice(prefix.length).toLowerCase();
      const value = envVars[key];

      // 数値に変換できる場合は数値として保存
      if (value && /^\d+$/.test(value)) {
        config[configKey] = parseInt(value, 10);
      } else if (value === 'true') {
        config[configKey] = true;
      } else if (value === 'false') {
        config[configKey] = false;
      } else {
        config[configKey] = value;
      }
    }
  }

  return config;
};
