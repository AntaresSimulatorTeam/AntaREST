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

import { createContext, useContext } from "react";
import type { Actions, State } from "use-undo";
import type { DataState } from "../hooks/useMatrixData";

export interface MatrixContextValue {
  // Data
  data: number[][];
  //aggregates: Partial<MatrixAggregates>;
  //columns: EnhancedGridColumn[];
  //dateTime: string[];
  //rowCount: number;

  // State
  //error?: Error;
  //isLoading: boolean;
  isSubmitting: boolean;
  updateCount: number;

  // Actions
  //handleCellEdit: (update: GridUpdate) => void;
  //handleMultipleCellsEdit: (updates: GridUpdate[]) => void;
  //handleUpload: (file: File) => Promise<void>;
  //handleSaveUpdates: () => Promise<void>;

  // History
  currentState: State<DataState>["present"];
  setState: Actions<DataState>["set"];
  undo: Actions<DataState>["undo"];
  redo: Actions<DataState>["redo"];
  canUndo: Actions<DataState>["canUndo"];
  canRedo: Actions<DataState>["canRedo"];
}

const MatrixContext = createContext<MatrixContextValue | undefined>(undefined);

export function MatrixProvider({
  children,
  ...value
}: React.PropsWithChildren<MatrixContextValue>) {
  return <MatrixContext.Provider value={value}>{children}</MatrixContext.Provider>;
}

export function useMatrixContext() {
  const context = useContext(MatrixContext);

  if (!context) {
    throw new Error("useMatrixContext must be used within MatrixProvider");
  }

  return context;
}
