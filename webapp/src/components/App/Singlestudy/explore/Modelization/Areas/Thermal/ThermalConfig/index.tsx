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

import { Chip, Divider } from "@mui/material";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import type { StudyMetadata } from "../../../../../../../../types/types";
import ThermalForm from "./ThermalForm";
import ThermalMatrices from "./ThermalMatrices";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import useNavigateOnCondition from "../../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "../../../../../../../../services/utils";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import BackButton from "@/components/common/buttons/BackButton";
import { useTranslation } from "react-i18next";

function ThermalConfig() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { clusterId = "" } = useParams();
  const { t } = useTranslation();

  useNavigateOnCondition({
    deps: [areaId],
    to: "../thermal",
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <BackButton onClick={() => navigate("../thermal")} />
      <ThermalForm study={study} areaId={areaId} clusterId={clusterId} />
      <Divider sx={{ mt: 1 }} variant="middle">
        <Chip label={t("global.matrices")} size="small" />
      </Divider>
      <ThermalMatrices study={study} areaId={areaId} clusterId={nameToId(clusterId)} />
    </ViewWrapper>
  );
}

export default ThermalConfig;
