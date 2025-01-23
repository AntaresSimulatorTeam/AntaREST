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

import { useMemo, useState } from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import { type MatrixItem, type StudyMetadata } from "../../../../../../../common/types";
import type { Storage } from "./utils";
import SplitView from "../../../../../../common/SplitView";
import Matrix from "../../../../../../common/Matrix";

interface Props {
  study: StudyMetadata;
  areaId: StudyMetadata["id"];
  storageId: Storage["id"];
}

function StorageMatrices({ areaId, storageId }: Props) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("modulation");

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
  };

  const MATRICES: MatrixItem[] = useMemo(
    () => [
      {
        titleKey: "modulation",
        content: {
          type: "split",
          matrices: [
            {
              url: `input/st-storage/series/${areaId}/${storageId}/pmax_injection`,
              titleKey: "injectionModulation",
            },
            {
              url: `input/st-storage/series/${areaId}/${storageId}/pmax_withdrawal`,
              titleKey: "withdrawalModulation",
            },
          ],
        },
      },
      {
        titleKey: "ruleCurves",
        content: {
          type: "split",
          matrices: [
            {
              url: `input/st-storage/series/${areaId}/${storageId}/lower_rule_curve`,
              titleKey: "lowerRuleCurve",
            },
            {
              url: `input/st-storage/series/${areaId}/${storageId}/upper_rule_curve`,
              titleKey: "upperRuleCurve",
            },
          ],
        },
      },
      {
        titleKey: "inflows",
        content: {
          type: "single",
          matrix: {
            url: `input/st-storage/series/${areaId}/${storageId}/inflows`,
            titleKey: "inflows",
          },
        },
      },
    ],
    [areaId, storageId],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexDirection: "column", width: 1, height: 1 }}>
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ width: 1 }}>
        {MATRICES.map(({ titleKey }) => (
          <Tab
            key={titleKey}
            value={titleKey}
            label={t(`study.modelization.storages.${titleKey}`)}
          />
        ))}
      </Tabs>
      <Box sx={{ height: 1, pt: 1 }}>
        {MATRICES.map(
          ({ titleKey, content }) =>
            activeTab === titleKey && (
              <Box key={titleKey} sx={{ height: 1 }}>
                {content.type === "split" ? (
                  <SplitView
                    id={`storage-${content.matrices[0].titleKey}-${content.matrices[1].titleKey}`}
                    sizes={[50, 50]}
                  >
                    {content.matrices.map(({ url, titleKey }) => (
                      <Box key={titleKey} sx={{ px: 2 }}>
                        <Matrix url={url} title={t(`study.modelization.storages.${titleKey}`)} />
                      </Box>
                    ))}
                  </SplitView>
                ) : (
                  <Matrix
                    key={content.matrix.titleKey}
                    url={content.matrix.url}
                    title={t(`study.modelization.storages.${content.matrix.titleKey}`)}
                  />
                )}
              </Box>
            ),
        )}
      </Box>
    </Box>
  );
}

export default StorageMatrices;
