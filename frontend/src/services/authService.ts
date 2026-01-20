/**
 * Authentication Service
 * 
 * Handles all authentication-related API calls including:
 * - Login/Logout
 * - Token management
 * - User registration
 * - Password management
 */

import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  user_id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'user';
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface TokenRefreshResponse {
  access_token: string;
  token_type: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

/**
 * Auth Service Class
 */
class AuthService {
  /**
   * Login user
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/api/auth/login`,
        { username, password }
      );

      // Store tokens and user info
      this.setAccessToken(response.data.access_token);
      this.setRefreshToken(response.data.refresh_token);
      this.setUserInfo(response.data.user);

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      const token = this.getAccessToken();
      if (token) {
        await axios.post(
          `${API_BASE_URL}/api/auth/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local storage
      this.clearAuth();
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post<TokenRefreshResponse>(
        `${API_BASE_URL}/api/auth/refresh`,
        { refresh_token: refreshToken }
      );

      this.setAccessToken(response.data.access_token);
      return response.data.access_token;
    } catch (error) {
      this.clearAuth();
      throw this.handleError(error);
    }
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<UserInfo> {
    try {
      const token = this.getAccessToken();
      if (!token) {
        throw new Error('No access token');
      }

      const response = await axios.get<UserInfo>(
        `${API_BASE_URL}/api/auth/me`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      this.setUserInfo(response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      const token = this.getAccessToken();
      if (!token) {
        throw new Error('No access token');
      }

      await axios.post(
        `${API_BASE_URL}/api/auth/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Token management methods
   */
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  setAccessToken(token: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }

  getUserInfo(): UserInfo | null {
    const userStr = localStorage.getItem(USER_INFO_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  setUserInfo(user: UserInfo): void {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
  }

  clearAuth(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  isAdmin(): boolean {
    const user = this.getUserInfo();
    return user?.role === 'admin';
  }

  /**
   * Error handler
   */
  private handleError(error: unknown): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      const message = axiosError.response?.data?.detail || axiosError.message;
      return new Error(message);
    }
    return error instanceof Error ? error : new Error('Unknown error');
  }
}

// Export singleton instance
export const authService = new AuthService();

/**
 * Axios interceptor for automatic token injection
 */
export const setupAxiosInterceptors = () => {
  // Request interceptor to add token
  axios.interceptors.request.use(
    (config) => {
      const token = authService.getAccessToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor to handle 401 errors
  axios.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as any;

      // If 401 and not already retried
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          // Try to refresh token
          const newToken = await authService.refreshToken();
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear auth and redirect to login
          authService.clearAuth();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );
};

export default authService;
