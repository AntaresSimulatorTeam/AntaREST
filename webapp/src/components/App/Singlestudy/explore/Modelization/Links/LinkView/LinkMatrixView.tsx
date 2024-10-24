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
import { Divider, styled } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";

export const StyledTab = styled(Tabs)({
  width: "100%",
  borderBottom: 1,
  borderColor: "divider",
});

interface Props {
  study: StudyMetadata;
  area1: string;
  area2: string;
}

function LinkMatrixView(props: Props) {
  const [t] = useTranslation();
  const { study, area1, area2 } = props;
  const [value, setValue] = React.useState(0);

  const columnsNames = [
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
  ];

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };
  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
    >
      <StyledTab
        value={value}
        onChange={handleChange}
        aria-label="basic tabs example"
      >
        <Tab label={t("study.modelization.links.matrix.parameters")} />
        <Tab label={t("study.modelization.links.matrix.capacities")} />
      </StyledTab>
      <Box
        sx={{
          display: "flex",
          width: "100%",
          height: "100%",
        }}
      >
        {value === 0 ? (
          <MatrixInput
            study={study}
            url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}_parameters`}
            columnsNames={columnsNames}
            computStats={MatrixStats.NOCOL}
          />
        ) : (
          <>
            <MatrixInput
              study={study}
              title={`${t(
                "study.modelization.links.matrix.columns.transCapaDirect",
              )} (${area1}->${area2})`}
              url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_direct`}
              computStats={MatrixStats.NOCOL}
            />
            <Divider sx={{ width: "1px", mx: 2, bgcolor: "divider" }} />
            <MatrixInput
              study={study}
              title={`${t(
                "study.modelization.links.matrix.columns.transCapaIndirect",
              )} (${area2}->${area1})`}
              url={`input/links/${area1.toLowerCase()}/capacities/${area2.toLowerCase()}_indirect`}
              computStats={MatrixStats.NOCOL}
            />
          </>
        )}
      </Box>
    </Box>
  );
}

export default LinkMatrixView;
