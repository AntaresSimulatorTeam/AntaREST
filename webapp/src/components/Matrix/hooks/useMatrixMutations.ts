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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormBlocker from "@/hooks/useFormBlocker";
import { updateMatrix } from "@/services/api/matrix";
import { uploadFile } from "@/services/api/studies/raw";
import { toError } from "@/utils/fnUtils";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AggregateType, GridUpdate } from "../shared/types";
import { calculateMatrixAggregates } from "../shared/utils";
import type { DataState, SetMatrixDataFunction } from "./useMatrixData";

interface UseMatrixMutationsProps {
  studyId: string;
  path: string;
  currentState: DataState;
  setMatrixData: SetMatrixDataFunction;
  isDirty: boolean;
  reload: VoidFunction; // check type
  aggregateTypes: AggregateType[];
}

interface MatrixMutationsResult {
  isSubmitting: boolean;
  handleCellEdit: (update: GridUpdate) => void;
  handleMultipleCellsEdit: (updates: GridUpdate[]) => void;
  handleUpload: (file: File) => Promise<void>;
  handleSaveUpdates: () => Promise<void>;
}

export function useMatrixMutations({
  studyId,
  path,
  currentState,
  setMatrixData,
  isDirty,
  reload,
  aggregateTypes,
}: UseMatrixMutationsProps): MatrixMutationsResult {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  // Prevents accidental navigation when matrix has unsaved changes or during submission
  useFormBlocker({ isSubmitting, isDirty });

  const updateMatrixData = useCallback(
    (updates: GridUpdate[]): void => {
      const updatedData = currentState.data.map((col) => [...col]);

      for (const {
        coordinates: [row, col],
        value,
      } of updates) {
        if (value.kind === "number" && value.data !== undefined) {
          updatedData[col][row] = value.data;
        }
      }

      const newAggregates = calculateMatrixAggregates({
        matrix: updatedData,
        types: aggregateTypes,
      });

      setMatrixData({
        data: updatedData,
        aggregates: newAggregates,
      });
    },
    [currentState, setMatrixData, aggregateTypes],
  );

  const handleCellEdit = useCallback(
    (update: GridUpdate) => {
      updateMatrixData([update]);
    },
    [updateMatrixData],
  );

  const handleMultipleCellsEdit = useCallback(
    (updates: GridUpdate[]) => {
      updateMatrixData(updates);
    },
    [updateMatrixData],
  );

  const handleUpload = useCallback(
    async (file: File) => {
      try {
        await uploadFile({ file, studyId, path: path });
        reload();
      } catch (error) {
        enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), toError(error));
      }
    },
    [studyId, path, reload, enqueueErrorSnackbar, t],
  );

  const handleSaveUpdates = useCallback(async () => {
    if (!isDirty) {
      return;
    }

    setIsSubmitting(true);
    try {
      const updatedMatrix = await updateMatrix(studyId, path, currentState.data);

      setMatrixData({
        ...currentState,
        data: updatedMatrix,
        saved: true,
      });
    } catch (error) {
      enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), toError(error));
    } finally {
      setIsSubmitting(false);
    }
  }, [isDirty, studyId, path, currentState, setMatrixData, enqueueErrorSnackbar, t]);

  return {
    isSubmitting,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleUpload,
    handleSaveUpdates,
  };
}
