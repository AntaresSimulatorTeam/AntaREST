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

import { Box } from "@mui/material";
import { forwardRef, useImperativeHandle, useMemo, useRef } from "react";
import { MatrixProvider } from "../context/MatrixContext";
import type { TimeFrequencyType } from "../shared/types";
import MatrixFilter, { type MatrixFilterHandle } from "./MatrixFilter";

import MatrixGrid, { type MatrixGridProps } from "./MatrixGrid";

export interface FilterableMatrixGridProps extends MatrixGridProps {
  timeFrequency?: TimeFrequencyType;
}

export interface FilterableMatrixGridHandle {
  toggleFilter: () => void;
}

function FilterableMatrixGrid(
  {
    data,
    rows,
    columns,
    dateTime,
    aggregates,
    rowHeaders,
    onCellEdit,
    onMultipleCellsEdit,
    readOnly = true,
    showPercent,
    showStats = true,
    timeFrequency,
  }: FilterableMatrixGridProps,
  ref: React.ForwardedRef<FilterableMatrixGridHandle>,
) {
  const matrixFilterRef = useRef<MatrixFilterHandle>(null);

  // Expose filter toggle functionality via ref
  useImperativeHandle(
    ref,
    () => ({
      toggleFilter: () => {
        matrixFilterRef.current?.toggle();
      },
    }),
    [],
  );

  // Create minimal context value for MatrixProvider
  // Only includes what's necessary for filtering functionality
  const contextValue = useMemo(
    () => ({
      // State required by MatrixProvider
      currentState: { data, aggregates: aggregates || {} },
      isSubmitting: false,
      updateCount: 0,
      aggregateTypes: [],

      // Stub implementations for functions we don't use
      setMatrixData: () => {
        // No-op: We don't modify data in this component
      },
      undo: () => {
        // No-op: No undo functionality needed
      },
      redo: () => {
        // No-op: No redo functionality needed
      },
      canUndo: false,
      canRedo: false,
      isDirty: false,
    }),
    [data, aggregates],
  );

  // Determine if this is a time series based on dateTime presence
  const isTimeSeries = !!dateTime && dateTime.length > 0;

  return (
    <MatrixProvider {...contextValue}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: 1,
          height: 1,
        }}
      >
        {/* Hidden MatrixFilter that can be triggered from outside via ref */}
        <Box sx={{ display: "none" }}>
          <MatrixFilter
            ref={matrixFilterRef}
            dateTime={dateTime}
            isTimeSeries={isTimeSeries}
            timeFrequency={timeFrequency}
            readOnly={readOnly}
          />
        </Box>

        <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <MatrixGrid
            data={data}
            rows={rows}
            columns={columns}
            dateTime={dateTime}
            aggregates={aggregates}
            rowHeaders={rowHeaders}
            width="100%"
            height="100%"
            onCellEdit={onCellEdit}
            onMultipleCellsEdit={onMultipleCellsEdit}
            readOnly={readOnly}
            showPercent={showPercent}
            showStats={showStats}
          />
        </Box>
      </Box>
    </MatrixProvider>
  );
}

export default forwardRef(FilterableMatrixGrid);
