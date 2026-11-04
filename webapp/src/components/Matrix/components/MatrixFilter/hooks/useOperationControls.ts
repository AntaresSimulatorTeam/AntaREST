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
import { useCallback } from "react";
import { Operation } from "../../../shared/constants";
import type { FilterState } from "../types";

interface UseOperationControlsProps {
  filter: FilterState;
  setOperation: React.Dispatch<React.SetStateAction<FilterState["operation"]>>;
}

export function useOperationControls({ filter, setOperation }: UseOperationControlsProps) {
  const canApplyOperation =
    filter.active &&
    Boolean(filter.columnsFilter.range || filter.columnsFilter.list?.length) &&
    (filter.operation.type === Operation.Abs || filter.operation.value !== undefined);

  const handleOperationTypeChange = useCallback(
    (operationType: string) => {
      setOperation(
        produce((draft) => {
          draft.type = operationType;
        }),
      );
    },
    [setOperation],
  );

  const handleValueChange = useCallback(
    (newValue: string) => {
      const parsed = Number.parseFloat(newValue);

      setOperation(
        produce((draft) => {
          draft.value = Number.isFinite(parsed) ? parsed : undefined;
        }),
      );
    },
    [setOperation],
  );

  return {
    value: filter.operation.value,
    canApplyOperation,
    handleOperationTypeChange,
    handleValueChange,
  };
}
