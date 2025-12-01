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

import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import { MATRICES, type HydroMatrixType } from "./utils";
import Matrix from "../../../../../../common/Matrix";
import { Box } from "@mui/material";

interface Props {
  type: HydroMatrixType;
}

function HydroMatrix({ type }: Props) {
  const areaId = useAppSelector(getCurrentAreaId);

  const hydroMatrix = MATRICES[type];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: 1, height: 1, p: 1 }}>
      <Matrix
        title={hydroMatrix.title}
        url={hydroMatrix.url.replace("{areaId}", areaId)}
        customColumns={hydroMatrix.columns}
        customRowHeaders={hydroMatrix.rowHeaders}
        aggregateColumns={hydroMatrix.aggregates}
        dateTimeColumn={hydroMatrix.dateTimeColumn}
        readOnly={hydroMatrix.readOnly}
        showPercent={hydroMatrix.showPercent}
        fetchMatrixData={hydroMatrix.fetchFn}
        rowCountSource={hydroMatrix.rowCountSource}
        isTimeSeries={hydroMatrix.isTimeSeries}
      />
    </Box>
  );
}

export default HydroMatrix;
