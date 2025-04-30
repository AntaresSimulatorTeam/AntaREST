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

import { useState } from "react";
import { Box, Button, TextField, Tooltip } from "@mui/material";
import { useUpdateEffect } from "react-use";
import Transform from "@mui/icons-material/Transform";
import { calculateMatrixAggregates, resizeMatrix } from "../shared/utils";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import { useMatrixContext } from "../context/MatrixContext";
import { clamp } from "ramda";

function MatrixResize() {
  const {
    currentState,
    setMatrixData,
    isSubmitting: isMatrixSubmitting,
    aggregateTypes,
  } = useMatrixContext();
  const { t } = useTranslation();
  const errorSnackBar = useEnqueueErrorSnackbar();
  const currentColumnCount = currentState.data[0].length;
  const [targetColumnCount, setTargetColumnCount] = useState(currentColumnCount);

  useUpdateEffect(() => {
    setTargetColumnCount(currentColumnCount);
  }, [currentColumnCount]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMatrixResize = () => {
    if (targetColumnCount === currentColumnCount) {
      return;
    }

    try {
      const updatedMatrix = resizeMatrix({
        matrix: currentState.data,
        newColumnCount: targetColumnCount,
      });

      setMatrixData({
        ...currentState,
        data: updatedMatrix,
        aggregates: calculateMatrixAggregates({ matrix: updatedMatrix, types: aggregateTypes }),
      });
    } catch (error) {
      errorSnackBar(t("matrix.error.matrixUpdate"), toError(error));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value);
    setTargetColumnCount(clamp(1, 1000, value));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <TextField
        type="number"
        size="extra-small"
        value={targetColumnCount}
        onChange={handleChange}
        disabled={isMatrixSubmitting}
        variant="outlined"
        sx={{
          width: 75,
          margin: 0,
        }}
        slotProps={{
          input: {
            inputProps: {
              min: 1,
              max: 1000,
            },
          },
        }}
      />
      <Tooltip title={t("matrix.resize")}>
        <span>
          <Button
            color="primary"
            variant="contained"
            onClick={handleMatrixResize}
            disabled={targetColumnCount === currentColumnCount || isMatrixSubmitting}
          >
            <Transform />
          </Button>
        </span>
      </Tooltip>
    </Box>
  );
}

export default MatrixResize;
