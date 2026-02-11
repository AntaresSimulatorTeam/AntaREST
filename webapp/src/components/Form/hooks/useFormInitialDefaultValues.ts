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

import { useCallback, useEffect, useRef } from "react";
import type { FieldValues, UseFormReturn } from "react-hook-form";

/**
 * Captures a stable snapshot of the form's original default values and exposes
 * a getter for that snapshot. The returned function always yields the defaults
 * that were present right after the form finished loading, even if:
 * - `reset()` is called with new values later on.
 * - default values arrive asynchronously.
 *
 * `formState.defaultValues` can be partial and mutates when `reset()` runs.
 *
 * @param formApi - The `useForm` return object.
 * @returns Function that returns the initial default values (or `undefined` while loading).
 */
function useFormInitialDefaultValues<TFieldValues extends FieldValues, TContext>(
  formApi: UseFormReturn<TFieldValues, TContext>,
) {
  const {
    formState: { isLoading, defaultValues },
    getValues,
  } = formApi;

  const getDefaultValues = (): TFieldValues => ({
    ...getValues(), // Because `formState.defaultValues` can be partial
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

  const getInitialDefaultValues = useCallback(() => initialDefaultValues.current, []);

  return getInitialDefaultValues;
}

export default useFormInitialDefaultValues;
