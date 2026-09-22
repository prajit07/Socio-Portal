import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import rawResources from './locales.json';

export const supportedLngs = ['en', 'hi', 'ta', 'te', 'ml', 'kn', 'mr', 'bn', 'gu', 'pa'];

// i18next expects resources as { lang: { namespace: { key: value } } }.
// locales.json stores a flat per-language key->value map, so nest it under
// the default 'translation' namespace.
const resources = Object.fromEntries(
  Object.entries(rawResources).map(([lng, keys]) => [lng, { translation: keys }])
);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    supportedLngs,
    fallbackLng: 'en',
    // Map browser codes like en-US / hi-IN to their base language
    load: 'languageOnly',
    nonExplicitSupportedLngs: true,
    // Empty-string translations fall back instead of rendering blank
    returnEmptyString: false,
    interpolation: {
      escapeValue: false, // React already safes from XSS
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    }
  });

export default i18n;
