import { StorageKeys } from '@/types/types';

export const setItem = <T>(key: StorageKeys, value: T): void => {
  localStorage.setItem(key, JSON.stringify(value));
};

export const getItem = (key: StorageKeys) => {
  try {
    const result = JSON.parse(localStorage.getItem(key) as string);
    return result;
  } catch (_) {
    return null;
  }
};

export const removeItem = (key: StorageKeys) => {
  return localStorage.removeItem(key);
};
