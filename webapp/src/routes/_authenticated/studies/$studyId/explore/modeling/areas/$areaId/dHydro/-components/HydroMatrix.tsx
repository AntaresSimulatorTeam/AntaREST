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

import Matrix from "@/components/Matrix";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { format } from "@/utils/stringUtils";
import { Box } from "@mui/material";
import { type HydroMatrixTypeValue, MATRICES } from "../-utils";
import useArea from "../../-hooks/useArea";

interface Props {
  type: HydroMatrixTypeValue;
}

function HydroMatrix({ type }: Props) {
  const study = useStudy();
  const area = useArea();
  const hydroMatrix = MATRICES[type];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: 1, height: 1, p: 1 }}>
      <Matrix
        key={area.id}
        studyId={study.id}
        title={hydroMatrix.title}
        url={format(hydroMatrix.url, { areaId: area.id })}
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
