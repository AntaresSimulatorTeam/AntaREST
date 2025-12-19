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

import Matrix from "@/components/Matrix";
import SplitView from "@/components/page/SplitView";
import TabsView from "@/components/page/TabsView";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../types/types";

interface Props {
  study: StudyMetadata;
  area1: string;
  area2: string;
  isOldStudy: boolean;
}

function LinkMatrices({ study, area1, area2, isOldStudy }: Props) {
  const { t } = useTranslation();

  if (isOldStudy) {
    return (
      <Matrix
        studyId={study.id}
        url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}`}
        customColumns={[
          t("study.modeling.links.matrix.columns.transCapaDirect"),
          t("study.modeling.links.matrix.columns.transCapaIndirect"),
          `${t("study.modeling.links.matrix.columns.hurdleCostsDirect")} (${area1}->${area2})`,
          `${t("study.modeling.links.matrix.columns.hurdleCostsIndirect")} (${area2}->${area1})`,
          t("study.modeling.links.matrix.columns.impedances"),
          t("study.modeling.links.matrix.columns.loopFlow"),
          t("study.modeling.links.matrix.columns.pShiftMin"),
          t("study.modeling.links.matrix.columns.pShiftMax"),
        ]}
      />
    );
  }

  return (
    <TabsView
      disableGutters
      tabs={[
        {
          id: "parameters",
          label: t("study.modeling.links.matrix.parameters"),
          content: (
            <Matrix
              studyId={study.id}
              url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}_parameters`}
              title={t("study.modeling.links.matrix.parameters")}
              customColumns={[
                `${t(
                  "study.modeling.links.matrix.columns.hurdleCostsDirect",
                )} (${area1}->${area2})`,
                `${t(
                  "study.modeling.links.matrix.columns.hurdleCostsIndirect",
                )} (${area2}->${area1})`,
                t("study.modeling.links.matrix.columns.impedances"),
                t("study.modeling.links.matrix.columns.loopFlow"),
                t("study.modeling.links.matrix.columns.pShiftMin"),
                t("study.modeling.links.matrix.columns.pShiftMax"),
              ]}
              isTimeSeries={false}
              enableFilters
            />
          ),
        },
        {
          id: "capacities",
          label: t("study.modeling.links.matrix.capacities"),
          content: (
            <SplitView splitId="link-transCapaDirect-transCapaIndirect" sizes={[50, 50]}>
              <Box sx={{ pr: 2 }}>
                <Matrix
                  studyId={study.id}
                  url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_direct`}
                  title={t("study.modeling.links.matrix.columns.transCapaDirect", {
                    area1,
                    area2,
                  })}
                />
              </Box>
              <Box sx={{ pl: 2 }}>
                <Matrix
                  studyId={study.id}
                  url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_indirect`}
                  title={t("study.modeling.links.matrix.columns.transCapaIndirect", {
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
