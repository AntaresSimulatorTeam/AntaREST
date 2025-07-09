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

import { createContext, useContext, useState, useEffect } from "react";
import type { Actions, State } from "use-undo";
import type { DataState, SetMatrixDataFunction } from "../hooks/useMatrixData";
import type { AggregateType } from "../shared/types";
import type { FilterCriteria } from "../components/MatrixFilter/types";

export interface MatrixContextValue {
  // State
  currentState: State<DataState>["present"];
  isSubmitting: boolean;
  updateCount: number;
  aggregateTypes: AggregateType[];

  // History
  setMatrixData: SetMatrixDataFunction;
  undo: Actions<DataState>["undo"];
  redo: Actions<DataState>["redo"];
  canUndo: Actions<DataState>["canUndo"];
  canRedo: Actions<DataState>["canRedo"];
  isDirty: boolean;

  // Filters
  filterPreview: {
    active: boolean;
    criteria: FilterCriteria;
  };
  setFilterPreview: (preview: { active: boolean; criteria: FilterCriteria }) => void;
}

/**
 * MatrixContext provides shared state and functionality for matrix components.
 *
 * This context is intentionally exported to support optional usage patterns:
 * - Components that REQUIRE matrix functionality (like MatrixActions) use useMatrixContext()
 *   which throws if context is missing
 * - Components that can work WITHOUT matrix functionality (like MatrixGrid) use useContext()
 *   directly and provide fallback behavior when context is undefined
 *
 * This design allows MatrixGrid to be used both:
 * 1. Within Matrix component (with full features like filtering, undo/redo)
 * 2. As a standalone component (basic grid functionality only)
 */
export const MatrixContext = createContext<MatrixContextValue | undefined>(undefined);

interface MatrixProviderProps {
  children: React.ReactNode;
  currentState: State<DataState>["present"];
  isSubmitting: boolean;
  updateCount: number;
  aggregateTypes: AggregateType[];
  setMatrixData: SetMatrixDataFunction;
  undo: Actions<DataState>["undo"];
  redo: Actions<DataState>["redo"];
  canUndo: Actions<DataState>["canUndo"];
  canRedo: Actions<DataState>["canRedo"];
  isDirty: boolean;
}

export function MatrixProvider({
  children,
  currentState,
  isSubmitting,
  updateCount,
  aggregateTypes,
  setMatrixData,
  undo,
  redo,
  canUndo,
  canRedo,
  isDirty,
}: MatrixProviderProps) {
  const [filterPreview, setFilterPreview] = useState<{
    active: boolean;
    criteria: FilterCriteria;
  }>(() => {
    const totalColumns = currentState.data[0]?.length || 0;
    const totalRows = currentState.data.length;

    return {
      active: false,
      criteria: {
        columnsIndices: Array.from({ length: totalColumns }, (_, i) => i),
        rowsIndices: Array.from({ length: totalRows }, (_, i) => i),
      },
    };
  });

  // Update filterPreview criteria when matrix data changes
  useEffect(() => {
    if (!filterPreview.active && currentState.data.length > 0) {
      const totalColumns = currentState.data[0]?.length || 0;
      const totalRows = currentState.data.length;

      setFilterPreview((prev) => ({
        ...prev,
        criteria: {
          columnsIndices: Array.from({ length: totalColumns }, (_, i) => i),
          rowsIndices: Array.from({ length: totalRows }, (_, i) => i),
        },
      }));
    }
  }, [currentState.data, filterPreview.active]);

  const value: MatrixContextValue = {
    currentState,
    isSubmitting,
    updateCount,
    aggregateTypes,
    setMatrixData,
    undo,
    redo,
    canUndo,
    canRedo,
    isDirty,
    filterPreview,
    setFilterPreview,
  };

  return <MatrixContext.Provider value={value}>{children}</MatrixContext.Provider>;
}

export function useMatrixContext() {
  const context = useContext(MatrixContext);

  if (!context) {
    throw new Error("useMatrixContext must be used within MatrixProvider");
  }

  return context;
}
