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

import { Button, Box, Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useState, useEffect } from "react";
import BasicDialog, { type BasicDialogProps } from "../../../../../../common/dialogs/BasicDialog";
import Matrix from "../../../../../../common/Matrix";
import type { HydroMatrixType } from "./utils";
import { getAllocationMatrix } from "./Allocation/utils";
import { getCorrelationMatrix } from "./Correlation/utils";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../../types/types";
import type { MatrixDataDTO } from "@/components/common/Matrix/shared/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type { AxiosError } from "axios";

interface AdaptedMatrixData {
  data: number[][];
  columns: string[];
  index: string[];
}

interface Props {
  open: boolean;
  onClose: () => void;
  type: HydroMatrixType;
}

const MATRIX_FETCHERS = {
  Allocation: getAllocationMatrix,
  Correlation: getCorrelationMatrix,
} as const;

function HydroMatrixDialog({ open, onClose, type }: Props) {
  /**
   * !TEMPORARY SOLUTION - Matrix Data Model Adaptation
   *
   * This component handles a specific case (Allocation, Correlation).
   * They receive their columns and row headers from the backend as numeric arrays.
   * This differs from the standard Matrix component usage where these properties expect string arrays
   * representing actual header labels.
   *
   * Current scenario:
   * - Backend returns {columns: number[], index: number[]} for these specific matrices
   * - Matrix component expects {columns: string[], rowHeaders: string[]} for its headers
   *
   * Future API model update will:
   * - Rename 'index' to 'rowHeaders' to better reflect its purpose
   * - Return properly formatted string arrays for header labels
   * - Allow using the standard HydroMatrix component without this adapter
   *
   * TODO - Once the API is updated:
   * 1. The model adapter layer will be removed
   * 2. These matrices will use the HydroMatrix component directly
   * 3. All matrices will follow the same data structure pattern
   */

  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const fetchFn = MATRIX_FETCHERS[type as keyof typeof MATRIX_FETCHERS];
  const [matrix, setMatrix] = useState<AdaptedMatrixData | undefined>(undefined);

  const matrixModelAdapter = (apiData: MatrixDataDTO): AdaptedMatrixData => ({
    data: apiData.data,
    columns: apiData.columns.map(String),
    index: apiData.index.map(String), // Will be renamed to rowHeaders in future API root
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchFn(study.id);
        setMatrix(matrixModelAdapter(data));
      } catch (error) {
        enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [study.id, type, t]);

  const dialogProps: BasicDialogProps = {
    open,
    onClose,
    actions: (
      <Button onClick={onClose} color="primary" variant="outlined">
        {t("global.close")}
      </Button>
    ),
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      {...dialogProps}
      contentProps={{
        sx: { p: 0, height: "90vh" },
      }}
      fullWidth
      maxWidth="xl"
    >
      <Box sx={{ width: 1, height: 1, p: 2 }}>
        {matrix ? (
          <Matrix
            title={`${type} Matrix`}
            url=""
            customColumns={matrix.columns}
            customRowHeaders={matrix.index}
            fetchMatrixData={fetchFn}
            readOnly
            dateTimeColumn={false}
            timeSeriesColumns={false}
            canImport
          />
        ) : (
          <Skeleton sx={{ height: 1, transform: "none" }} />
        )}
      </Box>
    </BasicDialog>
  );
}

export default HydroMatrixDialog;
