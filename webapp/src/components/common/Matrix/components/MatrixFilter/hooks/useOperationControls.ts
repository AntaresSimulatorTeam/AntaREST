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

import { useState, useCallback, useMemo } from "react";
import type { FilterState } from "../types";
import { Operation } from "../../../shared/constants";

interface UseOperationControlsProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
  onApplyOperation: () => void;
}

interface QuickOperation {
  label: string;
  op: string;
  value: number;
}

export function useOperationControls({
  filter,
  setFilter,
  onApplyOperation,
}: UseOperationControlsProps) {
  // Local state for the operation value to avoid unnecessary re-renders
  const [value, setValue] = useState<number>(filter.operation.value);

  // Define quick operations
  const quickOperations = useMemo<QuickOperation[]>(
    () => [
      { label: "+1", op: Operation.Add, value: 1 },
      { label: "-1", op: Operation.Sub, value: 1 },
      { label: "×2", op: Operation.Mul, value: 2 },
      { label: "÷2", op: Operation.Div, value: 2 },
      { label: "=0", op: Operation.Eq, value: 0 },
      { label: "|x|", op: Operation.Abs, value: 0 },
    ],
    [],
  );

  // Check if we have valid filters to apply operations
  const hasValidFilters = useMemo(
    () =>
      filter.active &&
      (filter.columnsFilter.range ||
        (filter.columnsFilter.list && filter.columnsFilter.list.length > 0)),
    [filter.active, filter.columnsFilter.range, filter.columnsFilter.list],
  );

  // Handle operation type change
  const handleOperationTypeChange = useCallback(
    (operationType: string) => {
      setFilter((prev) => ({
        ...prev,
        operation: {
          ...prev.operation,
          type: operationType,
        },
      }));
    },
    [setFilter],
  );

  // Handle value change from input
  const handleValueChange = useCallback(
    (newValue: number) => {
      setValue(newValue);
      setFilter((prev) => ({
        ...prev,
        operation: {
          ...prev.operation,
          value: newValue,
        },
      }));
    },
    [setFilter],
  );

  // Handle slider change
  const handleSliderChange = useCallback(
    (_event: Event, newValue: number | number[]) => {
      if (!Array.isArray(newValue)) {
        setValue(newValue);
        setFilter((prev) => ({
          ...prev,
          operation: {
            ...prev.operation,
            value: newValue,
          },
        }));
      }
    },
    [setFilter],
  );

  // Apply a quick operation
  const applyQuickOperation = useCallback(
    (op: string, val: number) => {
      setFilter((prev) => ({
        ...prev,
        operation: {
          type: op,
          value: val,
        },
      }));

      // Immediately apply the operation
      setTimeout(onApplyOperation, 0);
    },
    [setFilter, onApplyOperation],
  );

  return {
    value,
    quickOperations,
    hasValidFilters,
    handleOperationTypeChange,
    handleValueChange,
    handleSliderChange,
    applyQuickOperation,
  };
}
