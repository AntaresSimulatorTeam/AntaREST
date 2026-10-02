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

import { Stack } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import SplitHydroMatrix from "../-components/SplitHydroMatrix";
import { HydroMatrixType } from "../-utils";
import InflowStructureForm from "./-components/InflowStructureForm";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/inflow-structure/",
)({
  component: InflowStructure,
});

function InflowStructure() {
  return (
    <Stack direction="column" sx={{ height: 1 }}>
      <InflowStructureForm />
      <SplitHydroMatrix
        types={[HydroMatrixType.InflowPattern, HydroMatrixType.OverallMonthlyHydro]}
        direction="horizontal"
        sizes={[50, 50]}
      />
    </Stack>
  );
}
