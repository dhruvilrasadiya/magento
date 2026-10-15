export const routes = {
  home: '/',
  userManagement: '/user-management',
  chat: '/chat',
  chatSession: '/chat/:sessionId',
  usersList: '/users',
  login: '/login',
  pageNotFound: '*',
} as const;
