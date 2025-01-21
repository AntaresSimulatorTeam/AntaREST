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

import { useCallback } from "react";
import { Box, Button } from "@mui/material";
import { useParams, useOutletContext, useNavigate } from "react-router-dom";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../common/types";
import Form from "../../../../../../common/Form";
import Fields from "./Fields";
import Matrix from "./Matrix";
import { getRenewableCluster, updateRenewableCluster, type RenewableCluster } from "./utils";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import useNavigateOnCondition from "../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "../../../../../../../services/utils";

function Renewables() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { clusterId = "" } = useParams();

  useNavigateOnCondition({
    deps: [areaId],
    to: "../renewables",
  });

  // prevent re-fetch while useNavigateOnCondition event occurs
  const defaultValues = useCallback(() => {
    return getRenewableCluster(study.id, areaId, clusterId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<RenewableCluster>) => {
    return updateRenewableCluster(study.id, areaId, clusterId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
      <Button
        color="secondary"
        size="small"
        onClick={() => navigate("../renewables")}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start", mb: 1 }}
      >
        {t("button.back")}
      </Button>
      <Box sx={{ overflow: "auto" }}>
        <Form
          key={study.id + areaId}
          config={{ defaultValues }}
          onSubmit={handleSubmit}
          enableUndoRedo
        >
          <Fields />
        </Form>
        <Box
          sx={{
            height: "70vh",
          }}
        >
          <Matrix areaId={areaId} clusterId={nameToId(clusterId)} />
        </Box>
      </Box>
    </Box>
  );
}

export default Renewables;
