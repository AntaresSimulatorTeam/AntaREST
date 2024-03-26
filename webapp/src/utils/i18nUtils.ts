import i18n from "../i18n";

/**
 * Gets the current language used in the application.
 *
 * @returns The current language.
 */
export function getCurrentLanguage() {
  return i18n.language;
}

/**
 * Translates the given key and appends a colon (:) at the end
 * with the appropriate spacing for the current language.
 *
 * @param key - The translation key.
 * @returns The translated string with a colon (:) appended.
 */
export function translateWithColon(key: string): string {
  const lang = i18n.language;
  return `${i18n.t(key)}${lang.startsWith("fr") ? " " : ""}:`;
}
