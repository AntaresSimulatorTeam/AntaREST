import { t } from "i18next";

interface ValidationOptions {
  pattern?: RegExp;
  existingEntries?: string[];
  excludedEntries?: string[];
  isCaseSensitive?: boolean;
  min?: number;
  max?: number;
}

/**
 * Validates a single string value against specified options.
 *
 * @param {string} value - The string to validate, leading/trailing spaces will be trimmed.
 * @param {ValidationOptions} [options] - Customizable options for validation.
 *    - `pattern`: RegExp for matching the string. Default to alphanumeric, spaces and "&()_-" pattern.
 *    - `existingEntries`: Array of strings to check for duplicates. Optional, case-insensitive by default.
 *    - `excludedEntries`: Array of strings that are explicitly not allowed.
 *    - `isCaseSensitive`: Default to case-insensitive comparison with `existingEntries`. e.g: "A" and "a" are considered the same.
 *    - `min`: Minimum length required. Defaults to 0.
 *    - `max`: Maximum allowed length. Defaults to 50.
 * @returns {string | true} - True if validation is successful, or a localized error message if it fails.
 */
export const validateString = (
  value: string,
  options?: ValidationOptions,
): string | true => {
  const {
    pattern,
    existingEntries = [],
    excludedEntries = [],
    isCaseSensitive,
    min,
    max,
  } = {
    pattern: /^[a-zA-Z0-9_\-() &]+$/,
    isCaseSensitive: false,
    min: 0,
    max: 50,
    ...options,
  };

  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return t("form.field.required");
  }

  if (!pattern.test(trimmedValue)) {
    return t("form.field.specialChars", { 0: "&()_-" });
  }

  if (trimmedValue.length < min) {
    return t("form.field.minValue", { 0: min });
  }

  if (trimmedValue.length > max) {
    return t("form.field.maxValue", { 0: max });
  }

  const normalize = (entry: string) =>
    isCaseSensitive ? entry.trim() : entry.toLowerCase().trim();

  const comparisonArray = existingEntries.map(normalize);

  const comparisonValue = normalize(trimmedValue);

  if (comparisonArray.includes(comparisonValue)) {
    return t("form.field.duplicate", { 0: value });
  }

  const normalizedExcludedValues = excludedEntries.map(normalize);

  if (normalizedExcludedValues.includes(comparisonValue)) {
    return t("form.field.notAllowedValue", { 0: value });
  }

  return true;
};
