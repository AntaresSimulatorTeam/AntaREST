/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import * as React from "react";
import * as R from "ramda";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Storage } from "./utils";
import SplitLayoutView from "../../../../../../common/SplitLayoutView";

interface Props {
  study: StudyMetadata;
  areaId: StudyMetadata["id"];
  storageId: Storage["id"];
}

function Matrix({ study, areaId, storageId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = React.useState(0);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        width: 1,
        height: 1,
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
      }}
    >
      <Tabs sx={{ width: 1 }} value={value} onChange={(_, v) => setValue(v)}>
        <Tab label={t("study.modelization.storages.modulation")} />
        <Tab label={t("study.modelization.storages.ruleCurves")} />
        <Tab label={t("study.modelization.storages.inflows")} />
      </Tabs>
      <Box
        sx={{
          display: "flex",
          width: 1,
          height: 1,
        }}
      >
        {R.cond([
          [
            () => value === 0,
            () => (
              <SplitLayoutView
                left={
                  <MatrixInput
                    study={study}
                    url={`input/st-storage/series/${areaId}/${storageId}/pmax_injection`}
                    computStats={MatrixStats.NOCOL}
                    title={t("study.modelization.storages.injectionModulation")}
                  />
                }
                right={
                  <MatrixInput
                    study={study}
                    url={`input/st-storage/series/${areaId}/${storageId}/pmax_withdrawal`}
                    computStats={MatrixStats.NOCOL}
                    title={t(
                      "study.modelization.storages.withdrawalModulation",
                    )}
                  />
                }
                sx={{
                  mt: 1,
                  ".SplitLayoutView__Left": {
                    width: "50%",
                  },
                  ".SplitLayoutView__Right": {
                    height: 1,
                    width: "50%",
                  },
                }}
              />
            ),
          ],
          [
            () => value === 1,
            () => (
              <SplitLayoutView
                left={
                  <MatrixInput
                    study={study}
                    url={`input/st-storage/series/${areaId}/${storageId}/lower_rule_curve`}
                    computStats={MatrixStats.NOCOL}
                    title={t("study.modelization.storages.lowerRuleCurve")}
                  />
                }
                right={
                  <MatrixInput
                    study={study}
                    url={`input/st-storage/series/${areaId}/${storageId}/upper_rule_curve`}
                    computStats={MatrixStats.NOCOL}
                    title={t("study.modelization.storages.upperRuleCurve")}
                  />
                }
                sx={{
                  mt: 1,
                  ".SplitLayoutView__Left": {
                    width: "50%",
                  },
                  ".SplitLayoutView__Right": {
                    height: 1,
                    width: "50%",
                  },
                }}
              />
            ),
          ],
          [
            R.T,
            () => (
              <MatrixInput
                study={study}
                url={`input/st-storage/series/${areaId}/${storageId}/inflows`}
                computStats={MatrixStats.NOCOL}
                title={t("study.modelization.storages.inflows")}
              />
            ),
          ],
        ])()}
      </Box>
    </Box>
  );
}

export default Matrix;
