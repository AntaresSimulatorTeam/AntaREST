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

import type { DataGridProps } from "@/components/DataGrid";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import type { DataEditorProps, GridColumn, Item } from "@glideapps/glide-data-grid";
import type { ButtonProps, SxProps, Theme } from "@mui/material";
import type { Actions } from "use-undo";

export type Data = Record<string, Record<string, string | boolean | number>>;

export interface DataGridFormState {
  isDirty: boolean;
  isSubmitting: boolean;
}

export interface DataGridFormApi<TData extends Data> {
  data: TData;
  setData: Actions<TData>["set"];
  formState: DataGridFormState;
}

export interface Changes<TData extends Data> {
  /** Rows present in the current data but not in the saved data, keyed by row ID. */
  added: Partial<TData>;
  /** Rows present in both, containing only the values that differ from the saved data, keyed by row ID. */
  updated: { [K in keyof TData]?: Partial<TData[K]> };
  /** IDs of rows present in the saved data but no longer in the current data. */
  // Typed as `string` rather than `keyof TData`, which can include numbers,
  // because object keys are always strings at runtime.
  deleted: string[];
}

export interface DataGridFormSubmitData<TData extends Data = Data>
  extends Omit<SubmitHandlerPlus<TData>, "dirtyValues"> {
  dirtyValues: Changes<TData>["updated"];
  /** Row-level changes: added, updated and deleted rows */
  changes: Changes<TData>;
  /**
   * Marks a row as saved as soon as its request succeeds.
   * Useful when `onSubmit` sends several requests: if one fails, the rows
   * already saved won't be included again in the next submit's changes.
   */
  markAsSaved: (rowName: string) => void;
}

export interface DataGridFormProps<TData extends Data = Data, SubmitReturnValue = unknown> {
  defaultData: TData;
  columns: ReadonlyArray<GridColumn & { id: keyof TData[string] }>;
  rowMarkers?: DataGridProps["rowMarkers"];
  allowedFillDirections?: DataGridProps["allowedFillDirections"];
  onRowAppended?: DataGridProps["onRowAppended"];
  trailingRowOptions?: DataGridProps["trailingRowOptions"];
  enableColumnResize?: boolean;
  getCellContent?: (
    location: Item,
    data: TData[string][keyof TData[string]],
  ) => ReturnType<DataEditorProps["getCellContent"]>;
  /**
   * Transforms an edited value before it's stored.
   *
   * Called for each edited cell (typing, paste, fill or delete).
   *
   * @param location - The edited cell, as `[col, row]`.
   * @param newValue - The value entered in the cell.
   * @param data - The data before the edit. When several cells are edited at once
   * (paste or fill), it doesn't include the new values of the other edited cells.
   * @returns The value to store instead, or `undefined` to store the entered value as is.
   */
  transformCellValue?: (
    location: Item,
    newValue: unknown,
    data: TData,
  ) => TData[string][keyof TData[string]] | undefined;
  onSubmit: (
    data: DataGridFormSubmitData<TData>,
    event: React.SubmitEvent<HTMLFormElement>,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: DataGridFormSubmitData<TData>,
    submitResult: SubmitReturnValue,
  ) => void;
  onDataChange?: (data: TData) => void;
  onStateChange?: (state: DataGridFormState) => void;
  id?: string;
  sx?: SxProps<Theme>;
  extraActions?: React.ReactNode | ((state: { canSubmit: boolean }) => React.ReactNode);
  apiRef?: React.Ref<DataGridFormApi<TData>>;
  submitButtonText?: string;
  submitButtonIcon?: ButtonProps["startIcon"];
  hideSubmitButton?: boolean;
  disableErrorSnackbar?: boolean;
  isLoading?: boolean;
  readOnly?: boolean;
  allowRowDeletion?: boolean;
}
