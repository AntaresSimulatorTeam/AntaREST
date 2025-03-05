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
import { Tabs, Tab, Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { MatrixItem, StudyMetadata } from "../../../../../../../types/types";
import SplitView from "../../../../../../common/SplitView";
import Matrix from "../../../../../../common/Matrix";

interface Props {
  study: StudyMetadata;
  area1: string;
  area2: string;
}

function LinkMatrixView({ area1, area2 }: Props) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("parameters");

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
  };

  const MATRICES: MatrixItem[] = useMemo(
    () => [
      {
        titleKey: "parameters",
        content: {
          type: "single",
          matrix: {
            url: `input/links/${area1.toLowerCase()}/${area2.toLowerCase()}_parameters`,
            titleKey: "parameters",
            columnsNames: [
              `${t(
                "study.modelization.links.matrix.columns.hurdleCostsDirect",
              )} (${area1}->${area2})`,
              `${t(
                "study.modelization.links.matrix.columns.hurdleCostsIndirect",
              )} (${area2}->${area1})`,
              t("study.modelization.links.matrix.columns.impedances"),
              t("study.modelization.links.matrix.columns.loopFlow"),
              t("study.modelization.links.matrix.columns.pShiftMin"),
              t("study.modelization.links.matrix.columns.pShiftMax"),
            ],
          },
        },
      },
      {
        titleKey: "capacities",
        content: {
          type: "split",
          matrices: [
            {
              url: `input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_direct`,
              titleKey: "transCapaDirect",
            },
            {
              url: `input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_indirect`,
              titleKey: "transCapaIndirect",
            },
          ],
        },
      },
    ],
    [area1, area2, t],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", width: 1, height: 1 }}>
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ width: 1 }}>
        {MATRICES.map(({ titleKey }) => (
          <Tab
            key={titleKey}
            value={titleKey}
            label={t(`study.modelization.links.matrix.${titleKey}`)}
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
                    id={`link-${content.matrices[0].titleKey}-${content.matrices[1].titleKey}`}
                    sizes={[50, 50]}
                  >
                    {content.matrices.map(({ url, titleKey }) => (
                      <Box key={titleKey} sx={{ px: 2 }}>
                        <Matrix
                          url={url}
                          title={t(`study.modelization.links.matrix.columns.${titleKey}`, {
                            area1,
                            area2,
                          })}
                        />
                      </Box>
                    ))}
                  </SplitView>
                ) : (
                  <Matrix
                    key={content.matrix.titleKey}
                    url={content.matrix.url}
                    title={t(`study.modelization.links.matrix.${content.matrix.titleKey}`)}
                    customColumns={content.matrix.columnsNames}
                  />
                )}
              </Box>
            ),
        )}
      </Box>
    </Box>
  );
}

export default LinkMatrixView;
