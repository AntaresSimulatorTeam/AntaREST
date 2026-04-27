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
  // Local state allows clearing the field (undefined = empty/cleared).
  const [value, setValue] = useState<number | undefined>(filter.operation.value);

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
    (newValue: string) => {
      const parsed = Number.parseFloat(newValue);

      if (Number.isFinite(parsed)) {
        setValue(parsed);
        setFilter(
          produce((draft) => {
            draft.operation.value = parsed;
          }),
        );
      } else {
        setValue(undefined);
      }
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
