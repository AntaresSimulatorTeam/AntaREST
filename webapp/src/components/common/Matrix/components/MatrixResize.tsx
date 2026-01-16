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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import TransformIcon from "@mui/icons-material/Transform";
import { Button } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import FieldEditorButtonGroup from "../../FieldEditorButtonGroup";
import NumberFE from "../../fieldEditors/NumberFE";
import { useMatrixContext } from "../context/MatrixContext";
import { calculateMatrixAggregates, resizeMatrix } from "../shared/utils";

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
        aggregates: calculateMatrixAggregates({
          matrix: updatedMatrix,
          types: aggregateTypes,
        }),
      });
    } catch (error) {
      errorSnackBar(t("matrix.error.matrixUpdate"), toError(error));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value);
    setTargetColumnCount(R.clamp(1, 1000, value));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FieldEditorButtonGroup size="extra-small" tooltip={t("global.resize")}>
      <NumberFE
        value={targetColumnCount}
        onChange={handleChange}
        disabled={isMatrixSubmitting}
        sx={{ width: 75 }}
      />
      <Button
        onClick={handleMatrixResize}
        disabled={targetColumnCount === currentColumnCount || isMatrixSubmitting}
      >
        <TransformIcon />
      </Button>
    </FieldEditorButtonGroup>
  );
}

export default MatrixResize;
