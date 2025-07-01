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

import { produce } from "immer";
import { useCallback, useMemo, useState } from "react";
import type { FilterState } from "../types";

interface UseOperationControlsProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
  onApplyOperation: () => void;
}

export function useOperationControls({
  filter,
  setFilter,
  onApplyOperation,
}: UseOperationControlsProps) {
  // Local state for the operation value to avoid unnecessary re-renders
  const [value, setValue] = useState<number>(filter.operation.value);

  const hasValidFilters = useMemo(
    () =>
      filter.active &&
      (filter.columnsFilter.range ||
        (filter.columnsFilter.list && filter.columnsFilter.list.length > 0)),
    [filter.active, filter.columnsFilter.range, filter.columnsFilter.list],
  );

  const handleOperationTypeChange = useCallback(
    (operationType: string) => {
      setFilter(
        produce((draft) => {
          draft.operation.type = operationType;
        }),
      );
    },
    [setFilter],
  );

  const handleValueChange = useCallback(
    (newValue: number) => {
      setValue(newValue);
      setFilter(
        produce((draft) => {
          draft.operation.value = newValue;
        }),
      );
    },
    [setFilter],
  );

  return {
    value,
    hasValidFilters,
    handleOperationTypeChange,
    handleValueChange,
    onApplyOperation,
  };
}
