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
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../types/types";
import Matrix from "../../../../../../common/Matrix";
import SplitView from "../../../../../../common/SplitView";

interface Props {
  study: StudyMetadata;
  area1: string;
  area2: string;
  isOldStudy: boolean;
}

function LinkMatrices({ area1, area2, isOldStudy }: Props) {
  const { t } = useTranslation();

  if (isOldStudy) {
    return (
      <Matrix
        url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}`}
        customColumns={[
          t("study.modelization.links.matrix.columns.transCapaDirect"),
          t("study.modelization.links.matrix.columns.transCapaIndirect"),
          `${t("study.modelization.links.matrix.columns.hurdleCostsDirect")} (${area1}->${area2})`,
          `${t("study.modelization.links.matrix.columns.hurdleCostsIndirect")} (${area2}->${area1})`,
          t("study.modelization.links.matrix.columns.impedances"),
          t("study.modelization.links.matrix.columns.loopFlow"),
          t("study.modelization.links.matrix.columns.pShiftMin"),
          t("study.modelization.links.matrix.columns.pShiftMax"),
        ]}
      />
    );
  }

  return (
    <TabsView
      disableGutters
      items={[
        {
          label: t("study.modelization.links.matrix.parameters"),
          content: () => (
            <Matrix
              url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}_parameters`}
              title={t("study.modelization.links.matrix.parameters")}
              customColumns={[
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
              ]}
              isTimeSeries={false}
            />
          ),
        },
        {
          label: t("study.modelization.links.matrix.capacities"),
          content: () => (
            <SplitView id="link-transCapaDirect-transCapaIndirect" sizes={[50, 50]}>
              <Box sx={{ pr: 2 }}>
                <Matrix
                  url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_direct`}
                  title={t("study.modelization.links.matrix.columns.transCapaDirect", {
                    area1,
                    area2,
                  })}
                />
              </Box>
              <Box sx={{ pl: 2 }}>
                <Matrix
                  url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_indirect`}
                  title={t("study.modelization.links.matrix.columns.transCapaIndirect", {
                    area1,
                    area2,
                  })}
                />
              </Box>
            </SplitView>
          ),
        },
      ]}
    />
  );
}

export default LinkMatrices;
