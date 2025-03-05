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
import type { StudyMetadata } from "@/types/types";
import RenewableForm from "./RenewableForm";
import RenewableMatrix from "./RenewableMatrix";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "@/redux/selectors";
import useNavigateOnCondition from "../../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "@/services/utils";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import BackButton from "@/components/common/buttons/BackButton";
import { useTranslation } from "react-i18next";

function RenewableConfig() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { clusterId = "" } = useParams();
  const { t } = useTranslation();

  useNavigateOnCondition({
    deps: [areaId],
    to: "../renewables",
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <BackButton onClick={() => navigate("../renewables")} />
      <RenewableForm study={study} areaId={areaId} clusterId={nameToId(clusterId)} />
      <Divider sx={{ mt: 1 }} variant="middle">
        <Chip label={t("global.matrix")} size="small" />
      </Divider>
      <RenewableMatrix areaId={areaId} clusterId={nameToId(clusterId)} />
    </ViewWrapper>
  );
}

export default RenewableConfig;
