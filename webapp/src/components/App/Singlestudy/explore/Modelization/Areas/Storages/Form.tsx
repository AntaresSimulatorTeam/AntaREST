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
import * as RA from "ramda-adjunct";
import type { StudyMetadata } from "../../../../../../../common/types";
import Form from "../../../../../../common/Form";
import Fields from "./Fields";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import { getStorage, updateStorage, type Storage } from "./utils";
import Matrix from "./Matrix";
import useNavigateOnCondition from "../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "../../../../../../../services/utils";

function Storages() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { storageId = "" } = useParams();

  useNavigateOnCondition({
    deps: [areaId],
    to: `../storages`,
  });

  // prevent re-fetch while useNavigateOnCondition event occurs
  const defaultValues = useCallback(
    async () => {
      const storage = await getStorage(study.id, areaId, storageId);
      return {
        ...storage,
        // Convert to percentage ([0-1] -> [0-100])
        efficiency: storage.efficiency * 100,
        initialLevel: storage.initialLevel * 100,
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<Storage>) => {
    const newValues = { ...dirtyValues };
    // Convert to ratio ([0-100] -> [0-1])
    if (RA.isNumber(newValues.efficiency)) {
      newValues.efficiency /= 100;
    }
    if (RA.isNumber(newValues.initialLevel)) {
      newValues.initialLevel /= 100;
    }
    return updateStorage(study.id, areaId, storageId, newValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexDirection: "column", overflow: "auto" }}>
      <Button
        color="secondary"
        size="small"
        onClick={() => navigate("../storages")}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start", mb: 1 }}
      >
        {t("button.back")}
      </Button>
      <Box sx={{ overflow: "auto" }}>
        <Form
          key={study.id + areaId}
          config={{
            defaultValues,
          }}
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
          <Matrix study={study} areaId={areaId} storageId={nameToId(storageId)} />
        </Box>
      </Box>
    </Box>
  );
}

export default Storages;
