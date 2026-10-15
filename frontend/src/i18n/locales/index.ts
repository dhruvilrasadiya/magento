import commonEn from './en/common.json';
import authEn from './en/auth.json';
import usersEn from './en/users.json';
import chatEn from './en/chat.json';

import commonNl from './nl/common.json';
import authNl from './nl/auth.json';
import usersNl from './nl/users.json';
import chatNl from './nl/chat.json';

export const resources = {
  en: {
    common: commonEn,
    auth: authEn,
    users: usersEn,
    chat: chatEn,
  },
  nl: {
    common: commonNl,
    auth: authNl,
    users: usersNl,
    chat: chatNl,
  },
} as const;

export type Resources = typeof resources;
