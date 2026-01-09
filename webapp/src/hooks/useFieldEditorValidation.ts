/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { ValidateResult } from "react-hook-form";
import { useTranslation } from "react-i18next";
import useDebouncedState from "./useDebouncedState";

interface ValidationState {
  validity: ValidityState;
  isValid: boolean;
  validationMessage: string;
}

const defaultValidationState: ValidationState = {
  validity: {
    valueMissing: false,
    typeMismatch: false,
    patternMismatch: false,
    tooLong: false,
    tooShort: false,
    rangeUnderflow: false,
    rangeOverflow: false,
    stepMismatch: false,
    badInput: false,
    customError: false,
    valid: true,
  },
  isValid: true,
  validationMessage: "",
};

interface UseFieldEditorValidationParams<T extends HTMLInputElement | HTMLTextAreaElement> {
  customValidation?: (event: React.ChangeEvent<T>) => ValidateResult;
}

/**
 * Hook intended for use inside a field editor component (such as a custom input or textarea).
 * It centralizes and manages validation logic, combining both native browser validation
 * and custom validation rules.
 * This simplifies the implementation of robust, user-friendly validation in reusable
 * field editor components.
 *
 * `onInvalid` event handler is triggered on the input/textarea element when validation fails.
 *
 * Warning: `validationState` should not be accessed inside the `onChange` event handler,
 * because it may not be up-to-date during the event. Instead, use `event.target.validity`
 * and `event.target.validationMessage` for real-time validation feedback within the handler.
 *
 * @example
 * ```tsx
 * function OddNumberFE({ onChange, onBlur }: Props) {
 *   const {
 *     validateOnChange,
 *     validateOnBlur,
 *     validationState: { isValid, validationMessage },
 *   } = useFieldEditorValidation({
 *     customValidation: (event: React.ChangeEvent<HTMLInputElement>) => {
 *       return Number(event.target.value) % 2 === 0 ? "The number must be odd" : true;
 *     },
 *   });
 *
 *   return (
 *     <div>
 *       <input
 *         type="number"
 *         onChange={validateOnChange(onChange)}
 *         onBlur={validateOnBlur(onBlur)}
 *         style={{
 *           border: isValid ? "initial" : "1px solid red",
 *         }}
 *       />
 *       {!isValid && <div style={{ color: "red" }}>{validationMessage}</div>}
 *     </div>
 *   );
 * }
 * ```
 *
 * @param params - Parameters.
 * @param [params.customValidation] - Validation for custom validity.
 * @returns An object with the following properties:
 * - `validateOnChange`: Function wrapper for `onChange` event handler.
 * - `validateOnBlur`: Function wrapper for `onBlur` event handler.
 * - `validationState`: A state object containing:
 *   - `validity`: The `ValidityState` of the input element.
 *   - `isValid`: Boolean indicating if the input is valid (same as `validity.valid`).
 *   - `validationMessage`: The validation message to display.
 */
function useFieldEditorValidation<T extends HTMLInputElement | HTMLTextAreaElement>({
  customValidation,
}: UseFieldEditorValidationParams<T>) {
  const [validationState, setValidationState] = useDebouncedState(defaultValidationState, 1000);
  const { t } = useTranslation();

  const validateOnChange =
    (onChange?: React.ChangeEventHandler<T>) => (event: React.ChangeEvent<T>) => {
      if (customValidation) {
        const result = customValidation(event);

        // Custom validity (`event.target.validity.customError`).
        // `setCustomValidity` modifies `event.target.validity.customError`
        // and `event.target.validationMessage`.
        if (typeof result === "string" || result === false) {
          event.target.setCustomValidity(
            typeof result === "string" ? result : t("form.field.invalidValue"),
          );
        } else {
          event.target.setCustomValidity("");
        }
      }

      // Call after custom validation to ensure `event.target` is up-to-date.
      // `onChange` may rely on `event.target.validity.customError`
      // or `event.target.validationMessage`.
      onChange?.(event);

      // Check custom and native validity.
      // Note: `checkValidity()` allows also to trigger `onInvalid` event handler on element.
      if (!event.target.checkValidity()) {
        setValidationState((prev) => ({
          ...prev,
          validity: event.target.validity,
          isValid: false,
          validationMessage: event.target.validationMessage,
        }));
        return;
      }

      setValidationState(defaultValidationState);
      setValidationState.flush();
    };

  const validateOnBlur = (onBlur?: React.FocusEventHandler<T>) => (event: React.FocusEvent<T>) => {
    // Update validation state immediately on blur
    setValidationState.flush();

    onBlur?.(event);
  };

  return { validateOnChange, validateOnBlur, validationState };
}

export default useFieldEditorValidation;
