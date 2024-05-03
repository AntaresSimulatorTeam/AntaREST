import { useState } from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import {
  Cluster,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { COMMON_MATRIX_COLS, TS_GEN_MATRIX_COLS } from "./utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function Matrix({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = useState(0);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

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
      <Tabs sx={{ width: 1 }} value={value} onChange={handleChange}>
        <Tab label={t("study.modelization.clusters.matrix.common")} />
        <Tab label={t("study.modelization.clusters.matrix.tsGen")} />
        <Tab label={t("study.modelization.clusters.matrix.timeSeries")} />
        <Tab label={t("study.modelization.clusters.matrix.fuelCost")} />
        <Tab label={t("study.modelization.clusters.matrix.co2Cost")} />
      </Tabs>
      <Box
        sx={{
          display: "flex",
          width: 1,
          height: 1,
        }}
      >
        {value === 0 && (
          <MatrixInput
            study={study}
            url={`input/thermal/prepro/${areaId}/${clusterId}/modulation`}
            computStats={MatrixStats.NOCOL}
            title={t("study.modelization.clusters.matrix.common")}
            columnsNames={COMMON_MATRIX_COLS}
          />
        )}
        {value === 1 && (
          <MatrixInput
            study={study}
            url={`input/thermal/prepro/${areaId}/${clusterId}/data`}
            computStats={MatrixStats.NOCOL}
            title={t("study.modelization.clusters.matrix.tsGen")}
            columnsNames={TS_GEN_MATRIX_COLS}
          />
        )}
        {value === 2 && (
          <MatrixInput
            study={study}
            url={`input/thermal/series/${areaId}/${clusterId}/series`}
            computStats={MatrixStats.NOCOL}
            title={t("study.modelization.clusters.matrix.timeSeries")}
          />
        )}
        {value === 3 && (
          <MatrixInput
            study={study}
            url={`input/thermal/series/${areaId}/${clusterId}/fuelCost`}
            computStats={MatrixStats.NOCOL}
            title={t("study.modelization.clusters.matrix.fuelCost")}
          />
        )}
        {value === 4 && (
          <MatrixInput
            study={study}
            url={`input/thermal/series/${areaId}/${clusterId}/CO2Cost`}
            computStats={MatrixStats.NOCOL}
            title={t("study.modelization.clusters.matrix.co2Cost")}
          />
        )}
      </Box>
    </Box>
  );
}

export default Matrix;
