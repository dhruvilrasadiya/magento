import { useTranslation } from 'react-i18next';
import { Resources } from '@/i18n/locales';

export function useTranslations(namespace: keyof Resources['en'] = 'common') {
  return useTranslation(namespace);
}
