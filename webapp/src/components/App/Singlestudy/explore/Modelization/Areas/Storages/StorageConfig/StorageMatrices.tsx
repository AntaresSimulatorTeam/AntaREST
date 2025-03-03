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
import { type StudyMetadata } from "@/types/types";
import type { Storage } from "../utils";
import SplitView from "../../../../../../../common/SplitView";
import Matrix from "../../../../../../../common/Matrix";
import TabsView from "@/components/common/TabsView";

interface Props {
  study: StudyMetadata;
  areaId: StudyMetadata["id"];
  storageId: Storage["id"];
}

function StorageMatrices({ areaId, storageId }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      items={[
        {
          label: t("study.modelization.storages.modulation"),
          content: () => (
            <SplitView id="storage-injectionModulation-withdrawalModulation" sizes={[50, 50]}>
              <Box sx={{ pr: 2 }}>
                <Matrix
                  title={t("study.modelization.storages.injectionModulation")}
                  url={`input/st-storage/series/${areaId}/${storageId}/pmax_injection`}
                />
              </Box>
              <Box sx={{ pl: 2 }}>
                <Matrix
                  title={t("study.modelization.storages.withdrawalModulation")}
                  url={`input/st-storage/series/${areaId}/${storageId}/pmax_withdrawal`}
                />
              </Box>
            </SplitView>
          ),
        },
        {
          label: t("study.modelization.storages.ruleCurves"),
          content: () => (
            <SplitView id="storage-lowerRuleCurve-upperRuleCurve" sizes={[50, 50]}>
              <Box sx={{ pr: 2 }}>
                <Matrix
                  title={t("study.modelization.storages.lowerRuleCurve")}
                  url={`input/st-storage/series/${areaId}/${storageId}/lower_rule_curve`}
                />
              </Box>
              <Box sx={{ pl: 2 }}>
                <Matrix
                  title={t("study.modelization.storages.upperRuleCurve")}
                  url={`input/st-storage/series/${areaId}/${storageId}/upper_rule_curve`}
                />
              </Box>
            </SplitView>
          ),
        },
        {
          label: t("study.modelization.storages.inflows"),
          content: () => <Matrix url={`input/st-storage/series/${areaId}/${storageId}/inflows`} />,
        },
      ]}
    />
  );
}

export default StorageMatrices;
