/**
 * 表単状態管理サービス
 * バックエンドAPIと連携して表単状態を更新・取得
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export type FormStatus = 'pending' | 'submitted' | 'cancelled' | 'completed' | 'error';

export interface FormStatusUpdateRequest {
  form_status: FormStatus;
  form_data?: Record<string, any>;
  execution_result?: Record<string, any>;
}

export interface FormStatusResponse {
  success: boolean;
  data: {
    message_id: string;
    metadata: {
      form_status: FormStatus;
      form_data?: Record<string, any>;
      submitted_at?: string;
      cancelled_at?: string;
      completed_at?: string;
      execution_result?: any;
    };
  };
  message: string;
}

/**
 * 表単状態を更新
 */
export const updateFormStatus = async (
  messageId: string,
  formStatus: FormStatus,
  formData?: Record<string, any>,
  executionResult?: Record<string, any>
): Promise<FormStatusResponse> => {
  try {
    const response = await axios.patch<FormStatusResponse>(
      `${API_BASE_URL}/api/chat/messages/${messageId}/form-status`,
      {
        form_status: formStatus,
        form_data: formData,
        execution_result: executionResult
      }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to update form status:', error);
    throw error;
  }
};

/**
 * メッセージを取得
 */
export const getMessage = async (messageId: string): Promise<FormStatusResponse> => {
  try {
    const response = await axios.get<FormStatusResponse>(
      `${API_BASE_URL}/api/chat/messages/${messageId}`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to get message:', error);
    throw error;
  }
};
