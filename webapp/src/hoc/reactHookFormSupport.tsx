/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

/* eslint-disable @typescript-eslint/no-explicit-any */
import FieldSkeleton from "@/components/common/fieldEditors/FieldSkeleton";
import hoistNonReactStatics from "hoist-non-react-statics";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import React, { useContext, useMemo } from "react";
import {
  Controller,
  type ControllerRenderProps,
  type FieldPath,
  type FieldPathValue,
  type FieldValues,
  type Validate,
  type ValidateResult,
} from "react-hook-form";
import FormContext from "../components/common/Form/FormContext";
import type { ControlPlus, RegisterOptionsPlus } from "../components/common/Form/types";
import type { FakeBlurEventHandler, FakeChangeEventHandler } from "../utils/feUtils";
import { getComponentDisplayName } from "../utils/reactUtils";

interface ReactHookFormSupport<TValue> {
  defaultValue?: NonNullable<TValue> | ((props: any) => NonNullable<TValue>);
  setValueAs?: (value: any) => any;
  preValidate?: (value: any, formValues: any) => ValidateResult;
}

// `...args: any` allows to be compatible with all field editors
type EventHandler = (...args: any[]) => void;

interface FieldEditorProps<TValue> {
  value?: TValue;
  defaultValue?: TValue;
  onChange?: EventHandler;
  onBlur?: EventHandler;
  name?: string;
  disabled?: boolean;
  helperText?: React.ReactNode;
  error?: boolean;
  inputRef?: React.Ref<any>;
}

export type ReactHookFormSupportProps<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  TContext = any,
> =
  | {
      control: ControlPlus<TFieldValues, TContext>;
      rules?: Omit<
        RegisterOptionsPlus<TFieldValues, TFieldName>,
        // cf. UseControllerProps#rules
        | "valueAsNumber"
        | "valueAsDate"
        | "disabled"
        // Not necessary
        | "onBlur"
      >;
      shouldUnregister?: boolean;
      name: TFieldName;
    }
  | {
      control?: undefined;
      rules?: never;
      shouldUnregister?: never;
    };

// Allow to prevent to start with a space
const defaultSetValueAs = (v: any) => (typeof v === "string" ? v.trimStart() : v);

/**
 * Provides React Hook Form support to a field editor component, enhancing it with form control and validation capabilities.
 * It integrates custom validation logic, value transformation, and handles form submission state.
 *
 * @param options - Configuration options for the hook support.
 * @param options.preValidate - A function that pre-validates the value before the main validation.
 * @param options.setValueAs - A function that transforms the value before setting it into the form.
 * @returns A function that takes a field editor component and returns a new component wrapped with React Hook Form functionality.
 */
function reactHookFormSupport<TValue>(options: ReactHookFormSupport<TValue> = {}) {
  const { preValidate, setValueAs = defaultSetValueAs } = options;

  /**
   * Wraps the provided field editor component with React Hook Form functionality,
   * applying the specified pre-validation and value transformation logic.
   *
   * @param FieldEditor - The field editor component to wrap.
   * @returns The wrapped component with added React Hook Form support.
   */
  function withReactHookFormSupport<TProps extends FieldEditorProps<TValue>>(
    FieldEditor: React.ComponentType<TProps>,
  ) {
    /**
     * The wrapper component that integrates React Hook Form capabilities with the original field editor.
     * It manages form control registration, handles value changes and blurring with custom logic, and displays validation errors.
     *
     * @param props - The props of the field editor, extended with React Hook Form and custom options.
     * @returns The field editor component wrapped with React Hook Form functionality.
     */
    function WithReactHookFormSupport<
      TFieldValues extends FieldValues = FieldValues,
      TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
      TContext = any,
    >(props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> & TProps) {
      const { control, rules = {}, shouldUnregister, ...feProps } = props;

      const { validate, setValueAs: setValueAsFromRules = R.identity, ...restRules } = rules;

      const { isAutoSubmitEnabled } = useContext(FormContext);

      ////////////////////////////////////////////////////////////////
      // Event Handlers
      ////////////////////////////////////////////////////////////////

      const handleChange =
        (internalOnChange: ControllerRenderProps["onChange"]) =>
        (event: FakeChangeEventHandler) => {
          if (feProps.disabled) {
            return;
          }

          // Called here instead of Controller's rules, to keep original event
          feProps.onChange?.(event);

          // https://github.com/react-hook-form/react-hook-form/discussions/8068#discussioncomment-2415789
          // Data send back to hook form
          internalOnChange(
            setValueAsFromRules(
              setValueAs(
                event.target.type === "checkbox" ? event.target.checked : event.target.value,
              ),
            ),
          );
        };

      const handleBlur =
        (internalOnBlur: ControllerRenderProps["onBlur"]) => (event: FakeBlurEventHandler) => {
          if (feProps.disabled) {
            return;
          }

          // Called here instead of Controller's rules, to keep original event
          feProps.onBlur?.(event);

          // Report input has been interacted (focus and blur)
          internalOnBlur();
        };

      ////////////////////////////////////////////////////////////////
      // Utils
      ////////////////////////////////////////////////////////////////

      const validateWrapper = useMemo<
        RegisterOptionsPlus<TFieldValues, TFieldName>["validate"]
      >(() => {
        if (preValidate) {
          if (RA.isFunction(validate)) {
            return (value, formValues) => {
              const result = preValidate?.(value, formValues);

              if (typeof result === "string" || result === false) {
                return result;
              }

              return validate(value, formValues);
            };
          }

          if (RA.isPlainObj(validate)) {
            return Object.keys(validate).reduce(
              (acc, key) => {
                acc[key] = (value, formValues) => {
                  const result = preValidate?.(value, formValues);

                  if (typeof result === "string" || result === false) {
                    return result;
                  }

                  return validate[key](value, formValues);
                };
                return acc;
              },
              {} as Record<
                string,
                Validate<FieldPathValue<TFieldValues, TFieldName>, TFieldValues>
              >,
            );
          }

          return preValidate;
        }
        return validate;
      }, [validate]);

      const getDefaultValueFromOptions = () => {
        const { defaultValue } = options;
        return RA.isFunction(defaultValue) ? defaultValue(feProps) : defaultValue;
      };

      ////////////////////////////////////////////////////////////////
      // JSX
      ////////////////////////////////////////////////////////////////

      if (control && feProps.name) {
        const field = (
          <Controller
            control={control}
            name={feProps.name as TFieldName}
            // useForm's defaultValues take precedence
            defaultValue={(feProps.defaultValue ?? getDefaultValueFromOptions()) as any}
            rules={{ ...restRules, validate: validateWrapper }}
            shouldUnregister={shouldUnregister}
            render={({
              field: { ref, onChange, onBlur, ...fieldProps },
              fieldState: { error },
            }) => (
              <FieldEditor
                {...(feProps as TProps)}
                {...fieldProps}
                onChange={handleChange(onChange)}
                onBlur={handleBlur(onBlur)}
                inputRef={ref}
                error={!!error}
                helperText={error?.message || feProps.helperText}
                disabled={
                  (control._formState.isSubmitting && !isAutoSubmitEnabled) ||
                  fieldProps.disabled ||
                  feProps.disabled
                }
              />
            )}
          />
        );

        return control._formState.isLoading ? <FieldSkeleton>{field}</FieldSkeleton> : field;
      }

      return <FieldEditor {...(feProps as TProps)} />;
    }

    WithReactHookFormSupport.displayName = `WithReactHookFormSupport(${getComponentDisplayName(
      FieldEditor,
    )})`;

    return hoistNonReactStatics(WithReactHookFormSupport, FieldEditor);
  }

  return withReactHookFormSupport;
}

export default reactHookFormSupport;
