import { AxiosResponse } from 'axios';
import { JSX } from 'react';

//
// 🔗 Routing
//
export type RoutesType = {
  path: string;
  element: JSX.Element;
  children?: RoutesType[];
  primary?: boolean;
};

//
// 🧭 Menu
//
export type MenuItemsType = {
  label: string;
  icon: JSX.Element;
};

//
// 👤 User & Auth
//
export type Role = 'superadmin' | 'admin' | 'supervisor';

export type UserType = {
  email: string;
  password?: string;
  userName?: string;
  userId?: string;
  token?: string;
  RefreshToken?: string;
  role?: Role;
};

export type UserTokenPayload = {
  user_id: string;
  role: Role;
};

export type CreateUserPayload = {
  username: string;
  email: string;
  password: string;
  role: Role;
};

export type GetUsersType = CreateUserPayload & {
  id: string;
  created_at: Date;
};

export type GetUserResponse = {
  total: number;
  users: GetUsersType[];
};

export type DeleteAllUsersPayload = {
  user_ids: string[];
};

export type DeleteDialogType = {
  open: boolean;
  userId: string | null;
};

//
// 🔐 Auth API Payloads
//
export type LoginApiPayload = {
  username: string;
  password: string;
};

export type RefreshAccessTokenApiResponse = {
  access_token: string;
};

export type ForgetPasswordType = {
  email: string;
};

export type ResetPasswordType = {
  password: string;
  confirmPassword: string;
};

export type ResetPasswordPayload = {
  new_password: string;
  token: string;
};

export type FormType = 'Login' | 'ForgetPassword' | 'ResetPassword';

//
// 🔐 Permissions
//
export type SuperAdminPermissions =
  | 'create:admin'
  | 'create:user'
  | 'edit:admin'
  | 'delete:admin'
  | 'edit:all'
  | 'delete:all';

export type AdminPermissions =
  | 'create:supervisor'
  | 'create:user'
  | 'edit:supervisor'
  | 'delete:supervisor'
  | 'edit:all'
  | 'delete:all';

export type SupervisorPermissions = 'view';

export type Permissions = SuperAdminPermissions | AdminPermissions | SupervisorPermissions;

//
// 📦 Shared Utility Types
//
export type Order = 'asc' | 'desc';
export type SortableKey = 'username' | 'email' | 'role';

export type Sort = {
  order: Order;
  orderBy: SortableKey;
};

export type Pagination = {
  page: number;
  rowsPerPage: number;
  total: number;
};

export type StorageKeys = 'user';

//
// 💬 Chat & Sessions
//
export type MessageType = {
  id: string;
  isUser: boolean;
  text: string;
  timestamp: string;
};

export type MessagesType = {
  id: string;
  session_id: string;
  message: string;
  response: string;
  metadata: {
    selected_agent?: string[];
    agent_query?: Record<string, unknown>;
    sources?: Record<string, unknown>;
    email_output?: {
      email_data?: {
        to: string[];
        cc: string[];
        bcc: string[];
        subject: string;
        body: string;
        send_now: boolean;
      };
    };
  };
  timestamp: Date;
};

export type SessionType = {
  session_id: string;
  user_id: string;
  name?: string;
  messages?: MessagesType[];
  metadata: {
    selected_agent?: string[];
    agent_query?: Record<string, unknown>;
    sources?: Record<string, unknown>;
  };
  created_at: Date;
  last_activity: Date;
  total: number;
  offset: number;
  limit: number;
};

export type GetSessionApiResponse = {
  sessions: SessionType[];
};

export type UpdateSessionTitleApiPayload = {
  session_id: string;
  name: string;
};

export type SendQueryApiPayload = {
  query: string;
  session_id: string;
  modal_name: string;
  stream: boolean;
  language: string;
  auto_send_email?: boolean;
};

export type SendQueryApiResponse = {
  response: string;
  session_id: string;
  message_id: string;
  name?: string;
  metadata: Record<string, unknown>;
  timestamp: Date;
};

export type EmailData = {
  to: string[];
  cc: string[];
  bcc: string[];
  subject: string;
  message: string;
  isAlreadySent: boolean;
};

export type ChatEmailPayload = {
  email_data: {
    to: string[];
    cc: string[];
    bcc: string[];
    subject: string;
    body: string;
    session_id: string;
    message_id: string;
    send_now: boolean;
  };
};

//
// 📡 Generic API Wrapper
//
export type ApiResponse<T> = Promise<AxiosResponse<T>>;
