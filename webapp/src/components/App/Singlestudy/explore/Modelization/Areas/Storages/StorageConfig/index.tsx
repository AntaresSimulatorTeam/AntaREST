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

import BackButton from "@/components/common/buttons/BackButton";
import { getCurrentAreaId } from "@/redux/selectors";
import { nameToId } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import { Chip, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import useNavigateOnCondition from "../../../../../../../../hooks/useNavigateOnCondition";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import StorageForm from "./StorageForm";
import Matrix from "./StorageMatrices";

function StorageConfig() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { storageId = "" } = useParams();
  const { t } = useTranslation();

  useNavigateOnCondition({
    deps: [areaId],
    to: `../storages`,
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <BackButton onClick={() => navigate("../storages")} />
      <StorageForm study={study} areaId={areaId} storageId={storageId} />
      <Divider sx={{ my: 2 }} variant="middle">
        <Chip label={t("global.matrices")} size="small" />
      </Divider>
      <Matrix study={study} areaId={areaId} storageId={nameToId(storageId)} />
    </>
  );
}

export default StorageConfig;
