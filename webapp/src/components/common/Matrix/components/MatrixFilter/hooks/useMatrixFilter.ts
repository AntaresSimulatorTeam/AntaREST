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
import { useUpdateEffect } from "react-use";
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
  togglePreviewMode: (filteredData: FilterCriteria) => void;
  resetFilters: () => void;
  applyOperation: (filteredData: FilterCriteria) => void;
}

export function useMatrixFilter({
  rowCount,
  columnCount,
  timeFrequency,
}: UseMatrixFilterParams): UseMatrixFilterReturn {
  const { currentState, setMatrixData, aggregateTypes, setFilterPreview, filterPreview } =
    useMatrixContext();

  const [filter, setFilter] = useState<FilterState>(() =>
    getDefaultFilterState(rowCount, columnCount, timeFrequency),
  );

  const togglePreviewMode = useCallback(
    (filteredData: FilterCriteria) => {
      setFilterPreview({
        active: !filterPreview.active,
        criteria: filteredData,
      });
    },
    [filterPreview.active, setFilterPreview],
  );

  // Filter activation/deactivation effect
  useUpdateEffect(() => {
    if (!filter.active) {
      // Deactivate preview when filter is deactivated
      setFilterPreview({
        active: false,
        criteria: {
          columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
          rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
        },
      });
    }
  }, [filter.active, setFilterPreview, rowCount, columnCount]);

  const applyOperation = useCallback(
    (filteredData: FilterCriteria) => {
      if (!filter.active || currentState.data.length === 0) {
        return;
      }

      const { columnsIndices, rowsIndices } = filteredData;
      const { type: opType, value } = filter.operation;
      const newData = currentState.data.map((row) => [...row]);

      for (const rowIdx of rowsIndices) {
        for (const colIdx of columnsIndices) {
          const currentValue = newData[rowIdx][colIdx];

          switch (opType) {
            case Operation.Eq:
              newData[rowIdx][colIdx] = value;
              break;
            case Operation.Add:
              newData[rowIdx][colIdx] = currentValue + value;
              break;
            case Operation.Sub:
              newData[rowIdx][colIdx] = currentValue - value;
              break;
            case Operation.Mul:
              newData[rowIdx][colIdx] = currentValue * value;
              break;
            case Operation.Div:
              // Prevent division by zero
              if (value !== 0) {
                newData[rowIdx][colIdx] = currentValue / value;
              }
              break;
            case Operation.Abs:
              newData[rowIdx][colIdx] = Math.abs(currentValue);
              break;
          }
        }
      }

      setMatrixData({
        data: newData,
        aggregates: calculateMatrixAggregates({ matrix: newData, types: aggregateTypes }),
      });
    },
    [currentState.data, filter.active, filter.operation, setMatrixData, aggregateTypes],
  );

  const resetFilters = useCallback(() => {
    const newFilter = getDefaultFilterState(rowCount, columnCount, timeFrequency);

    setFilter(newFilter);

    setFilterPreview({
      active: false,
      criteria: {
        columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
        rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
      },
    });
  }, [rowCount, columnCount, timeFrequency, setFilterPreview]);

  const toggleFilter = useCallback(() => {
    setFilter((prev) => ({ ...prev, active: !prev.active }));
  }, []);

  return {
    filter,
    setFilter,
    toggleFilter,
    togglePreviewMode,
    resetFilters,
    applyOperation,
  };
}
