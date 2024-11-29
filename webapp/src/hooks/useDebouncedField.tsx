/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useState, useEffect, useCallback } from "react";
import useDebounce from "./useDebounce";

interface UseDebouncedFieldOptions<T> {
  value: T;
  onChange: (value: T) => void;
  delay: number;
  transformValue?: (value: T) => T;
}

interface UseDebouncedFieldResult<T> {
  localValue: T;
  handleChange: (value: T) => void;
  setLocalValue: (value: T) => void;
}

/**
 * A hook that implements a "locally controlled, parentally debounced" pattern for form fields.
 *
 * 1. Controlled by Parent:
 * - Parent owns the source of truth
 * - Hook syncs with parent value changes
 *
 * 2. Local State Benefits:
 * - Immediate UI feedback during typing
 * - No input lag
 *
 * 3. Debounced Updates:
 * - Parent updates (e.g. API calls) only trigger after user stops typing
 * - Prevents excessive updates during rapid changes
 *
 * @param options - Configuration object for the debounced field
 * @param options.value - The controlled value from parent
 * @param options.onChange - Callback to update parent value (debounced)
 * @param options.delay - Debounce delay in milliseconds (default: 500)
 * @param options.transformValue - Optional value transformation function
 
 * @returns Object containing:
 * - localValue: The immediate local state value
 * - handleChange: Function to handle value changes (with debouncing)
 * - setLocalValue: Function to directly update local value without debouncing
 *
 * @example
 * ```tsx
 * // Example with API calls
 * function SearchField({ onSearch }) {
 *   const { localValue, handleChange } = useDebouncedField({
 *     value: searchTerm,      // Parent control
 *     onChange: onSearch,     // Debounced API call
 *     delay: 500             // Wait 500ms after typing stops
 *   });
 *
 *   return (
 *     <input
 *       value={localValue}    // Immediate updates
 *       onChange={handleChange}
 *     />
 *   );
 * }
 * ```
 */
export function useDebouncedField<T>({
  value,
  onChange,
  delay = 500,
  transformValue,
}: UseDebouncedFieldOptions<T>): UseDebouncedFieldResult<T> {
  const [localValue, setLocalValue] = useState<T>(value);

  // Sync local value with prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const debouncedOnChange = useDebounce(onChange, delay);

  const handleChange = useCallback(
    (newValue: T) => {
      const value = transformValue?.(newValue) ?? newValue;
      setLocalValue(value);
      debouncedOnChange(value);
    },
    [debouncedOnChange, transformValue],
  );

  return {
    localValue,
    handleChange,
    setLocalValue,
  };
}
