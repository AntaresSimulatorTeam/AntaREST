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

import { useState, useCallback } from "react";
import { useMatrixContext } from "../../../context/MatrixContext";
import { Operation } from "../../../shared/constants";
import { calculateMatrixAggregates } from "../../../shared/utils";
import { getDefaultFilterState } from "../constants";
import type { FilterState, FilterCriteria } from "../types";
import type { TimeFrequencyType } from "../../../shared/types";

interface UseMatrixFilterParams {
  rowCount: number;
  columnCount: number;
  timeFrequency?: TimeFrequencyType;
}

interface UseMatrixFilterReturn {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
  toggleFilter: () => void;
  resetFilters: () => void;
  applyOperation: (filteredData: FilterCriteria) => void;
}

/**
 * Hook to manage matrix filter state and operations
 *
 * @param params - Matrix dimensions and time frequency
 * @param params.rowCount - Number of rows in the matrix
 * @param params.columnCount - Number of columns in the matrix
 * @param params.timeFrequency - Optional time frequency type
 * @returns Filter state and control functions
 */
export function useMatrixFilter({
  rowCount,
  columnCount,
  timeFrequency,
}: UseMatrixFilterParams): UseMatrixFilterReturn {
  const { currentState, setMatrixData, aggregateTypes, setFilterPreview } = useMatrixContext();

  const [filter, setFilter] = useState<FilterState>(() =>
    getDefaultFilterState(rowCount, columnCount, timeFrequency),
  );

  const toggleFilter = useCallback(() => {
    setFilter((prev) => ({ ...prev, active: !prev.active }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilter(getDefaultFilterState(rowCount, columnCount, timeFrequency));

    setFilterPreview({
      active: false,
      criteria: {
        columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
        rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
      },
    });
  }, [rowCount, columnCount, timeFrequency, setFilterPreview]);

  const applyOperation = useCallback(
    (filteredData: FilterCriteria) => {
      if (!filter.active || currentState.data.length === 0) {
        return;
      }

      const { columnsIndices, rowsIndices } = filteredData;
      const { type: opType, value: opValue } = filter.operation;

      const newData = currentState.data.map((row) => [...row]);

      // Apply operation to each selected cell
      for (const rowIdx of rowsIndices) {
        for (const colIdx of columnsIndices) {
          const currentValue = newData[rowIdx][colIdx];

          newData[rowIdx][colIdx] = applyOperationToValue(currentValue, opType, opValue);
        }
      }

      setMatrixData({
        data: newData,
        aggregates: calculateMatrixAggregates({ matrix: newData, types: aggregateTypes }),
      });
    },
    [currentState.data, filter.active, filter.operation, setMatrixData, aggregateTypes],
  );

  return {
    filter,
    setFilter,
    toggleFilter,
    resetFilters,
    applyOperation,
  };
}

/**
 * Applies an operation to a single value
 *
 * @param currentValue - The current value to apply the operation to
 * @param operationType - The type of operation to apply
 * @param operationValue - The value to use in the operation
 * @returns The result of applying the operation
 */
function applyOperationToValue(
  currentValue: number,
  operationType: string,
  operationValue: number,
): number {
  switch (operationType) {
    case Operation.Eq:
      return operationValue;

    case Operation.Add:
      return currentValue + operationValue;

    case Operation.Sub:
      return currentValue - operationValue;

    case Operation.Mul:
      return currentValue * operationValue;

    case Operation.Div:
      return operationValue !== 0 ? currentValue / operationValue : currentValue;

    case Operation.Abs:
      return Math.abs(currentValue);

    default:
      return currentValue;
  }
}
