import axios from '@/config/axiosConfig';
import {
  ApiResponse,
  SessionType,
  CreateUserPayload,
  ForgetPasswordType,
  GetSessionApiResponse,
  GetUserResponse,
  GetUsersType,
  ResetPasswordPayload,
  SendQueryApiPayload,
  SendQueryApiResponse,
  UpdateSessionTitleApiPayload,
  RefreshAccessTokenApiResponse,
  LoginApiPayload,
  DeleteAllUsersPayload,
  ChatEmailPayload,
} from '@/types/types';
import { GenericAbortSignal } from 'axios';

// Auth API
export const loginUser = (data: LoginApiPayload) => {
  return axios.post('/auth/login', data);
};

export const forgetPassword = (data: ForgetPasswordType) => {
  return axios.post('/auth/forgot-password', data);
};

export const resetPassword = (data: ResetPasswordPayload) => {
  return axios.post('/auth/reset-password', data);
};

export const refreshAccessToken = (
  refreshToken: string
): ApiResponse<RefreshAccessTokenApiResponse> => {
  return axios.post('/auth/refresh-token', { refresh_token: refreshToken });
};

// User Management API
export const createUser = (data: CreateUserPayload) => {
  return axios.post('/users', data);
};

export const getUsers = (
  page: number,
  limit: number,
  role?: string
): ApiResponse<GetUserResponse> => {
  const url = role
    ? `/users/?role=${encodeURIComponent(role)}&page=${page}&limit=${limit}`
    : `/users/?page=${page}&limit=${limit}`;
  return axios.get(url);
};

export const updateUser = (data: GetUsersType) => {
  return axios.patch(`/users/${data.id}`, data);
};

export const deleteUser = (id: string) => {
  return axios.delete(`/users/${id}`);
};

export const deleteAllUsers = (data: DeleteAllUsersPayload) => {
  return axios.delete('/users/delete-all', { data });
};

// Chat API
export const sendQuery = (data: SendQueryApiPayload): ApiResponse<SendQueryApiResponse> => {
  return axios.post('/chat/query', data);
};

export const createSession = (userId: string): ApiResponse<SessionType> => {
  return axios.post('/session', { user_id: userId });
};

export const getSessionsListByUserId = (
  userId: string,
  page: number,
  limit: number,
  signal: GenericAbortSignal,
  days?: number
): ApiResponse<GetSessionApiResponse> => {
  const params = new URLSearchParams({
    user_id: userId,
    offset: page.toString(),
    limit: limit.toString(),
  });

  if (days !== undefined) {
    params.append('days', days.toString());
  }

  return axios.get(`/session/list?${params.toString()}`, { signal });
};

export const getSessionBySessionId = (
  sessionId: string,
  skip: number,
  limit: number
): ApiResponse<SessionType> => {
  return axios.get(`/session/${sessionId}?skip=${skip}&limit=${limit}`);
};

export const deleteSessionBySessionId = (sessionId: string) => {
  return axios.delete(`/session/${sessionId}`);
};

export const updateSessionTitle = (data: UpdateSessionTitleApiPayload) => {
  return axios.patch(`/session/rename-session`, data);
};

export const sendEmail = (data: ChatEmailPayload) => {
  return axios.post('/chat/send-email', data);
};
