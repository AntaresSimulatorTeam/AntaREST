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

import * as RA from "ramda-adjunct";
import { useEffect, useMemo, useRef } from "react";
import type {
  BatchFieldArrayUpdate,
  FieldPath,
  FieldValue,
  FieldValues,
  Path,
  UseFormReturn,
  UseFormSetValue,
  UseFormUnregister,
} from "react-hook-form";
import useUpdatedRef from "../../../hooks/useUpdatedRef";
import type {
  AutoSubmitHandler,
  UseFormRegisterPlus,
  UseFormReturnPlus,
  UseFormSetValues,
} from "./types";

interface Params<TFieldValues extends FieldValues, TContext> {
  formApi: UseFormReturn<TFieldValues, TContext>;
  isAutoSubmitEnabled: boolean;
  fieldAutoSubmitListeners: React.MutableRefObject<
    Record<string, AutoSubmitHandler<FieldValue<TFieldValues>> | undefined>
  >;
  fieldsChangeDuringAutoSubmitting: React.MutableRefObject<Array<FieldPath<TFieldValues>>>;
  submit: VoidFunction;
}

function useFormApiPlus<TFieldValues extends FieldValues, TContext>(
  params: Params<TFieldValues, TContext>,
): UseFormReturnPlus<TFieldValues, TContext> {
  const { formApi, fieldAutoSubmitListeners, fieldsChangeDuringAutoSubmitting, ...data } = params;
  const { register, unregister, getValues, setValue, control, formState } = formApi;
  const { isSubmitting, isLoading, defaultValues } = formState;

  const getDefaultValues = (): TFieldValues => ({
    ...(control._formValues as TFieldValues), // Because `formState.defaultValues` can be partial
    ...defaultValues,
  });

  const initialDefaultValues = useRef(isLoading ? undefined : getDefaultValues());

  // Prevent to add the values in `useMemo`'s deps
  const dataRef = useUpdatedRef({
    ...data,
    // Don't read `formState` in `useMemo`. See `useEffect`'s comment below.
    isSubmitting,
  });

  // In case async default values has been given to the form.
  useEffect(
    () => {
      initialDefaultValues.current = getDefaultValues();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isLoading],
  );

  const formApiPlus = useMemo(
    () => {
      const registerWrapper: UseFormRegisterPlus<TFieldValues> = (name, options) => {
        if (options?.onAutoSubmit) {
          fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
        }

        const newOptions: typeof options = {
          ...options,
          onChange: (event: unknown) => {
            options?.onChange?.(event);

            if (dataRef.current.isAutoSubmitEnabled) {
              if (
                dataRef.current.isSubmitting &&
                !fieldsChangeDuringAutoSubmitting.current.includes(name)
              ) {
                fieldsChangeDuringAutoSubmitting.current.push(name);
              }

              dataRef.current.submit();
            }
          },
        };

        return register(name, newOptions);
      };

      const unregisterWrapper: UseFormUnregister<TFieldValues> = (name, options) => {
        if (dataRef.current.isAutoSubmitEnabled) {
          const names = RA.ensureArray(name) as Array<Path<TFieldValues>>;
          names.forEach((n) => {
            delete fieldAutoSubmitListeners.current[n];
          });
        }
        return unregister(name, options);
      };

      const setValueWrapper: UseFormSetValue<TFieldValues> = (name, value, options) => {
        const newOptions: typeof options = {
          shouldDirty: true, // False by default
          ...options,
        };

        if (dataRef.current.isAutoSubmitEnabled && newOptions.shouldDirty) {
          if (dataRef.current.isSubmitting) {
            fieldsChangeDuringAutoSubmitting.current.push(name);
          }
          // If it's a new value
          if (value !== getValues(name)) {
            dataRef.current.submit();
          }
        }

        setValue(name, value, newOptions);
      };

      const setValues: UseFormSetValues<TFieldValues> = (values, options) => {
        Object.keys(values).forEach((name) => {
          setValueWrapper(name as Path<TFieldValues>, values[name], options);
        });
      };

      const updateFieldArrayWrapper: BatchFieldArrayUpdate = (...args) => {
        control._setFieldArray(...args);
        if (dataRef.current.isAutoSubmitEnabled) {
          dataRef.current.submit();
        }
      };

      // Spreading cannot be used because getters and setters would be removed
      const controlPlus = new Proxy(control, {
        get(...args) {
          const prop = args[1];
          if (prop === "register") {
            return registerWrapper;
          }
          if (prop === "unregister") {
            return unregisterWrapper;
          }
          if (prop === "_updateFieldArray") {
            return updateFieldArrayWrapper;
          }
          return Reflect.get(...args);
        },
      });

      return {
        ...formApi,
        setValues,
        register: registerWrapper,
        unregister: unregisterWrapper,
        setValue: setValueWrapper,
        control: controlPlus,
        _internal: {
          get initialDefaultValues(): Readonly<TFieldValues> | undefined {
            return initialDefaultValues.current;
          },
        },
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [formApi],
  );

  // `formState` is wrapped with a Proxy and updated in batch.
  // The API is updated here to keep reference, like `useForm` return.
  // ! Don't used `useEffect`, because it's read before render.
  formApiPlus.formState = formState;

  return formApiPlus;
}

export default useFormApiPlus;
