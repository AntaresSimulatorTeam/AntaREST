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

import TabsView from "@/components/TabsView";
import { getCurrentAreaId } from "@/redux/selectors";
import { nameToId } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import AdditionalConstraints from "./AdditionalConstraints";
import StorageForm from "./StorageForm";
import StorageMatrices from "./StorageMatrices";

function StorageConfig() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { storageId = "" } = useParams();
  const { t } = useTranslation();
  const studyId = study.id;
  const studyVersion = Number(study.version);

  return (
    <TabsView
      onBack={() => navigate("../storages")}
      divider
      tabs={[
        {
          label: t("study.modelization.storages.operatingParameters"),
          content: (
            <StorageForm
              studyId={studyId}
              studyVersion={studyVersion}
              areaId={areaId}
              storageId={storageId}
            />
          ),
        },
        {
          label: t("global.timeSeries"),
          content: (
            <StorageMatrices studyVersion={studyVersion} areaId={areaId} storageId={storageId} />
          ),
        },
        studyVersion >= 920 && {
          label: t("study.modelization.storages.additionalConstraints"),
          content: (
            <AdditionalConstraints
              studyId={studyId}
              areaId={areaId}
              storageId={nameToId(storageId)}
              studyVersion={studyVersion}
            />
          ),
        },
      ].filter(Boolean)}
    />
  );
}

export default StorageConfig;
