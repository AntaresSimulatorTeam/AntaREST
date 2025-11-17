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
import type { PartialBy } from "@/utils/tsUtils";
import type {
  DeepPartial,
  FieldPath,
  FieldValues,
  SetValueConfig,
  UseFormReturn,
} from "react-hook-form";

export interface SubmitHandlerPlus<
  TFieldValues extends FieldValues = FieldValues,
  // Purpose of this parameter: https://github.com/react-hook-form/react-hook-form/issues/12447
  PossibleDisabledField extends FieldPath<TFieldValues> = never,
> {
  values: PartialBy<TFieldValues, PossibleDisabledField>;
  dirtyValues: Partial<TFieldValues>;
}

export type UseFormSetValues<TFieldValues extends FieldValues> = (
  values: DeepPartial<TFieldValues> | TFieldValues,
  options?: SetValueConfig,
) => void;

export interface UseFormReturnPlus<TFieldValues extends FieldValues = FieldValues, TContext = any>
  extends UseFormReturn<TFieldValues, TContext> {
  setValues: UseFormSetValues<TFieldValues>;
  _internal: {
    initialDefaultValues: Readonly<TFieldValues> | undefined;
  };
}
