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

import {
  getMatrixFilters,
  resetMatrixFilters,
  setMatrixFilters,
} from "@/redux/ducks/matrixFilters";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { Decimal } from "decimal.js-light";
import { produce } from "immer";
import { useCallback, useMemo, useState } from "react";
import { useMatrixContext } from "../../../context/MatrixContext";
import { Operation } from "../../../shared/constants";
import type { TimeFrequencyType } from "../../../shared/types";
import { calculateMatrixAggregates } from "../../../shared/utils";
import { getDefaultFilterState } from "../constants";
import type {
  FilterCriteria,
  FilterState,
  MatrixFilterPersistence,
  PersistedMatrixFilters,
} from "../types";

interface UseMatrixFilterParams {
  rowCount: number;
  columnCount: number;
  timeFrequency?: TimeFrequencyType;
  persistence?: MatrixFilterPersistence;
}

interface UseMatrixFilterReturn {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<PersistedMatrixFilters>>;
  setOperation: React.Dispatch<React.SetStateAction<FilterState["operation"]>>;
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
 * @param params.persistence - Optional study and logical view to remember filters for
 * @returns Filter state and control functions
 */
export function useMatrixFilter({
  rowCount,
  columnCount,
  timeFrequency,
  persistence,
}: UseMatrixFilterParams): UseMatrixFilterReturn {
  const { currentState, setMatrixData, aggregateTypes } = useMatrixContext();
  const dispatch = useAppDispatch();
  const studyId = persistence?.studyId;
  const key = persistence ? JSON.stringify([persistence.key, timeFrequency ?? null]) : undefined;

  const { defaultFilter, defaultOperation } = useMemo(() => {
    const { operation, ...settings } = getDefaultFilterState(rowCount, columnCount, timeFrequency);
    return { defaultFilter: settings, defaultOperation: operation };
  }, [rowCount, columnCount, timeFrequency]);
  // Unconfigured matrices retain local filters; operation controls are always local.
  const [localFilter, setLocalFilter] = useState(defaultFilter);
  const [operation, setOperation] = useState(defaultOperation);
  const savedFilters = useAppSelector((state) =>
    studyId && key ? getMatrixFilters(state, { studyId, key }) : undefined,
  );
  const filter = useMemo(
    () => ({ ...(studyId && key ? (savedFilters ?? defaultFilter) : localFilter), operation }),
    [studyId, key, savedFilters, defaultFilter, localFilter, operation],
  );

  const setFilter = useCallback<React.Dispatch<React.SetStateAction<PersistedMatrixFilters>>>(
    (update) => {
      if (!studyId || !key) {
        setLocalFilter(update);
        return;
      }

      // Read the latest store state so consecutive functional updates compose correctly.
      dispatch((dispatch, getState) => {
        const previous = getMatrixFilters(getState(), { studyId, key }) ?? defaultFilter;
        const next = typeof update === "function" ? update(previous) : update;

        if (next !== previous) {
          const { active, rowsFilters, columnsFilter } = next;
          dispatch(
            setMatrixFilters({ studyId, key, filters: { active, rowsFilters, columnsFilter } }),
          );
        }
      });
    },
    [dispatch, studyId, key, defaultFilter],
  );

  const toggleFilter = useCallback(() => {
    setFilter(
      produce((draft) => {
        draft.active = !draft.active;
      }),
    );
  }, [setFilter]);

  const resetFilters = useCallback(() => {
    if (studyId && key) {
      dispatch(resetMatrixFilters({ studyId, key }));
    }
    setLocalFilter(defaultFilter);
    setOperation(defaultOperation);
  }, [dispatch, studyId, key, defaultFilter, defaultOperation]);

  const applyOperation = useCallback(
    (filteredData: FilterCriteria) => {
      if (!filter.active || currentState.data.length === 0) {
        return;
      }

      const { columnsIndices, rowsIndices } = filteredData;
      const { type: opType, value: opValue } = filter.operation;

      if (opType !== Operation.Abs && opValue === undefined) {
        return;
      }

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
    setOperation,
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
  operationValue: number | undefined,
): number {
  if (operationType === Operation.Abs) {
    return Math.abs(currentValue);
  }

  if (operationValue === undefined) {
    return currentValue;
  }

  if (operationType === Operation.Eq) {
    return operationValue;
  }

  const a = new Decimal(currentValue);
  const b = new Decimal(operationValue);
  let result: Decimal;

  switch (operationType) {
    case Operation.Add:
      result = a.plus(b);
      break;
    case Operation.Sub:
      result = a.minus(b);
      break;
    case Operation.Mul:
      result = a.times(b);
      break;
    case Operation.Div:
      result = b.isZero() ? a : a.dividedBy(b);
      break;
    default:
      return currentValue;
  }

  return result.toDecimalPlaces(Math.max(a.decimalPlaces(), b.decimalPlaces())).toNumber();
}
