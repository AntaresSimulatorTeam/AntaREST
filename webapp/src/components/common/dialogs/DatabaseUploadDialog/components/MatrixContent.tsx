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

import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Box, Divider, Typography } from "@mui/material";
import type { MatrixInfoDTO, MatrixDTO } from "@/types/types";
import MatrixGrid from "@/components/common/Matrix/components/MatrixGrid";
import ButtonBack from "@/components/common/ButtonBack";
import { getMatrix } from "@/services/api/matrix";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { generateDataColumns } from "@/components/common/Matrix/shared/utils";
import EmptyView from "@/components/common/page/EmptyView";
import GridOffIcon from "@mui/icons-material/GridOff";
import { isNonEmptyMatrix } from "@/components/common/Matrix/shared/types";

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
