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
import type { DataState, SetMatrixDataFunction } from "../hooks/useMatrixData";
import type { AggregateType } from "../shared/types";

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
