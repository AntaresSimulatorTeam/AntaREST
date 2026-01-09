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

import { useEffect, useMemo, useRef } from "react";
import type { FieldValues, Path, UseFormReturn, UseFormSetValue } from "react-hook-form";
import type { UseFormReturnPlus, UseFormSetValues } from "./types";

function useFormApiPlus<TFieldValues extends FieldValues, TContext>(
  formApi: UseFormReturn<TFieldValues, TContext>,
): UseFormReturnPlus<TFieldValues, TContext> {
  const { setValue, control, formState } = formApi;
  const { isLoading, defaultValues } = formState;

  const getDefaultValues = (): TFieldValues => ({
    ...(control._formValues as TFieldValues), // Because `formState.defaultValues` can be partial
    ...defaultValues,
  });

  const initialDefaultValues = useRef(isLoading ? undefined : getDefaultValues());

  // In case async default values has been given to the form.
  useEffect(
    () => {
      initialDefaultValues.current = getDefaultValues();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isLoading],
  );

  const formApiPlus = useMemo(() => {
    const setValueWrapper: UseFormSetValue<TFieldValues> = (name, value, options) => {
      const newOptions: typeof options = {
        shouldDirty: true, // False by default
        ...options,
      };

      setValue(name, value, newOptions);
    };

    const setValues: UseFormSetValues<TFieldValues> = (values, options) => {
      Object.keys(values).forEach((name) => {
        setValueWrapper(name as Path<TFieldValues>, values[name], options);
      });
    };

    return {
      ...formApi,
      setValues,
      setValue: setValueWrapper,
      _internal: {
        get initialDefaultValues(): Readonly<TFieldValues> | undefined {
          return initialDefaultValues.current;
        },
      },
    };
  }, [formApi, setValue]);

  // `formState` is wrapped with a Proxy and updated in batch.
  // The API is updated here to keep reference, like `useForm` return.
  // ! Don't used `useEffect`, because it's read before render.
  formApiPlus.formState = formState;

  return formApiPlus;
}

export default useFormApiPlus;
