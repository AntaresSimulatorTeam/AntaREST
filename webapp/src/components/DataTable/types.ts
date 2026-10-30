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

import type { ToOptions } from "@tanstack/react-router";
import type { MRT_ColumnDef } from "material-react-table";

export interface RowData {
  id: string;
  name: string;
  group?: string;
}

export type MainRowData = Omit<RowData, "id">;

export interface BaseDataTableProps<TData extends RowData> {
  data: TData[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: Array<MRT_ColumnDef<TData, any>>;
  /**
   * Omit to disable grouping. When omitted, the group column and grouping
   * behavior are removed and the create dialog skips the group field.
   */
  groups?: string[];
  allowNewGroups?: boolean;
  onDuplicate?: (row: TData, newName: string) => void;
  onDelete?: (rows: TData[]) => void;
  onNameClick?: (row: TData) => void;
  nameLinkOptions?: (row: TData) => ToOptions;
  readOnly?: boolean;
  isLoading?: boolean;
  isSaving?: boolean;
  deleteConfirmationMessage?: string | ((rows: TData[]) => string);
  /**
   * Extra actions rendered next to the built-in Add/Duplicate/Delete buttons.
   */
  toolbarActions?: React.ReactNode;
}

export type DataTableProps<
  TData extends RowData,
  TCreateSubmitData = undefined,
> = BaseDataTableProps<TData> &
  (
    | {
        onCreate?: (mainData: MainRowData) => void;
        renderCreateDialog?: never;
      }
    | {
        onCreate: (mainData: MainRowData, customData: TCreateSubmitData) => void;
        /**
         * Render a custom create dialog instead of the built-in one.
         * Useful when creation requires fields the built-in dialog doesn't handle.
         */
        renderCreateDialog: (props: {
          open: boolean;
          onClose: VoidFunction;
          onSubmit: (mainData: MainRowData, customData: TCreateSubmitData) => void;
          existingNames: Array<RowData["name"]>;
        }) => React.ReactNode;
      }
  );
