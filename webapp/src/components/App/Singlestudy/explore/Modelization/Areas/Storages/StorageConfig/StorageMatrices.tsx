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

import TabsView from "@/components/common/TabsView";
import type { StudyMetadata } from "@/types/types";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import Matrix from "../../../../../../../common/Matrix";
import SplitView from "../../../../../../../common/SplitView";
import type { Storage } from "../utils";

interface Props {
  study: StudyMetadata;
  areaId: StudyMetadata["id"];
  storageId: Storage["id"];
  studyVersion: number;
}

// !NOTE: The Matrix components are configured with `isTimeSeries={false}` and
// `customColumns={["TS 1"]}` as a temporary solution. These are actually
// time series matrices, but the development for them has not been completed
// on the simulator side yet. When that development is done, these properties
// should be removed to restore the standard time series behavior with resize
// functionality.
function StorageMatrices({ areaId, storageId, studyVersion }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const matricesAllVersions = [
    {
      label: t("study.modelization.storages.modulation"),
      content: () => (
        <SplitView id="storage-injectionModulation-withdrawalModulation" sizes={[50, 50]}>
          <Box sx={{ pr: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.injectionModulation")}
              url={`input/st-storage/series/${areaId}/${storageId}/pmax_injection`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
          <Box sx={{ pl: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.withdrawalModulation")}
              url={`input/st-storage/series/${areaId}/${storageId}/pmax_withdrawal`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
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
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.lowerRuleCurve")}
              url={`input/st-storage/series/${areaId}/${storageId}/lower_rule_curve`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
          <Box sx={{ pl: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.upperRuleCurve")}
              url={`input/st-storage/series/${areaId}/${storageId}/upper_rule_curve`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
        </SplitView>
      ),
    },
    {
      label: t("study.modelization.storages.inflows"),
      content: () => (
        <Matrix
          url={`input/st-storage/series/${areaId}/${storageId}/inflows`}
          isTimeSeries={false}
          customColumns={["TS 1"]}
        />
      ),
    },
  ];

  const matrices920 = [
    {
      label: t("study.modelization.storages.costs"),
      content: () => (
        <SplitView id="storage-injectionCost-withdrawalCost" sizes={[50, 50]}>
          <Box sx={{ pr: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.injectionCost")}
              url={`input/st-storage/series/${areaId}/${storageId}/cost_injection`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
          <Box sx={{ pl: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.withdrawalCost")}
              url={`input/st-storage/series/${areaId}/${storageId}/cost_withdrawal`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
        </SplitView>
      ),
    },
    {
      label: t("study.modelization.storages.variationCosts"),
      content: () => (
        <SplitView id="storage-variationInjectionCost-variationWithdrawalCost" sizes={[50, 50]}>
          <Box sx={{ pr: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.injectionVariationCost")}
              url={`input/st-storage/series/${areaId}/${storageId}/cost_variation_injection`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
          <Box sx={{ pl: 2 }}>
            {/* TODO: Remove isTimeSeries={false} and customColumns when simulator development is complete */}
            <Matrix
              title={t("study.modelization.storages.withdrawalVariationCost")}
              url={`input/st-storage/series/${areaId}/${storageId}/cost_variation_withdrawal`}
              isTimeSeries={false}
              customColumns={["TS 1"]}
            />
          </Box>
        </SplitView>
      ),
    },
    {
      label: t("study.modelization.storages.levelCost"),
      content: () => (
        <Matrix
          title={t("study.modelization.storages.levelCost")}
          url={`input/st-storage/series/${areaId}/${storageId}/cost_level`}
          isTimeSeries={false}
          customColumns={["TS 1"]}
        />
      ),
    },
  ];

  return (
    <TabsView
      disableGutters
      items={[...matricesAllVersions, ...(studyVersion >= 920 ? matrices920 : [])]}
    />
  );
}

export default StorageMatrices;
