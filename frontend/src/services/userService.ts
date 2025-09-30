/**
 * User Management Service
 * 
 * Handles user-related API calls for admin users
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role: 'admin' | 'user';
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  role?: 'admin' | 'user';
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

class UserService {
  /**
   * Get list of users
   */
  async getUsers(
    page: number = 1,
    pageSize: number = 20,
    roleFilter?: string,
    search?: string
  ): Promise<UserListResponse> {
    try {
      const params: any = {
        page,
        page_size: pageSize
      };

      if (roleFilter) params.role_filter = roleFilter;
      if (search) params.search = search;

      const response = await axios.get<UserListResponse>(
        `${API_BASE_URL}/api/users/`,
        { params }
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get user by ID
   */
  async getUser(userId: number): Promise<User> {
    try {
      const response = await axios.get<User>(
        `${API_BASE_URL}/api/users/${userId}`
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create new user
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    try {
      const response = await axios.post<User>(
        `${API_BASE_URL}/api/users/`,
        userData
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Update user
   */
  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    try {
      const response = await axios.put<User>(
        `${API_BASE_URL}/api/users/${userId}`,
        userData
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Delete user
   */
  async deleteUser(userId: number): Promise<void> {
    try {
      await axios.delete(`${API_BASE_URL}/api/users/${userId}`);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Error handler
   */
  private handleError(error: unknown): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      return new Error(message);
    }
    return error instanceof Error ? error : new Error('Unknown error');
  }
}

export const userService = new UserService();
export default userService;
