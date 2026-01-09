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

import ButtonBack from "@/components/ButtonBack";
import MatrixGrid from "@/components/Matrix/components/MatrixGrid";
import { isNonEmptyMatrix } from "@/components/Matrix/shared/types";
import { generateDataColumns } from "@/components/Matrix/shared/utils";
import EmptyView from "@/components/page/EmptyView";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getMatrix } from "@/services/api/matrix";
import type { MatrixDTO, MatrixInfoDTO } from "@/types/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box, Divider, Typography } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

interface MatrixContentProps {
  matrixInfo: MatrixInfoDTO;
  onBack: () => void;
}

function MatrixContent({ matrixInfo, onBack }: MatrixContentProps) {
  const { t } = useTranslation();

  const { data: matrix } = usePromiseWithSnackbarError<MatrixDTO>(() => getMatrix(matrixInfo.id), {
    errorMessage: t("data.error.matrix"),
  });

  const matrixColumns = useMemo(
    () =>
      matrix
        ? generateDataColumns({
            isTimeSeries: true,
            count: matrix.columns.length,
          })
        : [],
    [matrix],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!matrix) {
    return null;
  }

  return (
    <>
      <Box sx={{ display: "flex" }}>
        <ButtonBack onClick={onBack} />
        <Typography>{matrixInfo.name}</Typography>
      </Box>
      <Divider sx={{ mt: 1, mb: 2 }} />
      {isNonEmptyMatrix(matrix.data) ? (
        <MatrixGrid data={matrix.data} columns={matrixColumns} rows={matrix.data.length} readOnly />
      ) : (
        <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOffIcon} />
      )}
    </>
  );
}

export default MatrixContent;
