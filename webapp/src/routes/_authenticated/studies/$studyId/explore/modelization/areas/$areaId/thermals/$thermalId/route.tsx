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

import BackButton from "@/components/buttons/BackButton";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { nameToId } from "@/services/utils";
import { Chip, Divider } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import ThermalForm from "./-components/ThermalForm";
import ThermalMatrices from "./-components/ThermalMatrices";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId",
)({
  component: ThermalConfig,
});

function ThermalConfig() {
  const study = useStudy();
  const area = useArea();
  const navigate = Route.useNavigate();
  const { thermalId } = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <BackButton onClick={() => navigate({ to: ".." })} />
      <ThermalForm study={study} areaId={area.id} clusterId={thermalId} />
      <Divider sx={{ my: 2 }} variant="middle">
        <Chip label={t("global.matrices")} size="small" />
      </Divider>
      <ThermalMatrices study={study} areaId={area.id} clusterId={nameToId(thermalId)} />
    </>
  );
}
