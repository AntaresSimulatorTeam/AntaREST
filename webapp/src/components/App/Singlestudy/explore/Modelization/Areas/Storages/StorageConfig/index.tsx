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

import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import BackButton from "@/components/common/buttons/BackButton";
import TabsView from "@/components/common/TabsView";
import { getCurrentAreaId } from "@/redux/selectors";
import { nameToId } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import AdditionalConstraints from "./AdditionalConstraints";
import StorageForm from "./StorageForm";

function StorageConfig() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { storageId = "" } = useParams();
  const { t } = useTranslation();
  // const studyVersion = Number(study.version);
  // TODO: conditionnal render of additional constraints only for studies > 9.2 ?

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <BackButton onClick={() => navigate("../storages")} />
      <Box sx={{ width: 1, height: "calc(100% - 45px)" }}>
        <TabsView
          divider
          items={[
            {
              label: t("study.modelization.storages.operatingParameters"),
              content: () => <StorageForm study={study} areaId={areaId} storageId={storageId} />,
            },
            {
              label: t("study.modelization.storages.additionalConstraints"),
              content: () => (
                <AdditionalConstraints
                  study={study}
                  areaId={areaId}
                  storageId={nameToId(storageId)}
                />
              ),
            },
          ]}
        />
      </Box>
    </>
  );
}

export default StorageConfig;
