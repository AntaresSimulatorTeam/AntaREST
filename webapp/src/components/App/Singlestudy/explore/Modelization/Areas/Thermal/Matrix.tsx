import * as React from "react";
import * as R from "ramda";
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

interface Props {
  study: StudyMetadata;
  areaId: string;
  clusterId: Cluster["id"];
}

function Matrix({ study, areaId, clusterId }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = React.useState(0);

  const commonNames = [
    "Marginal cost modulation",
    "Market bid modulation",
    "Capacity modulation",
    "Min gen modulation",
  ];

  const tsGenNames = [
    "FO Duration",
    "PO Duration",
    "FO Rate",
    "PO Rate",
    "NPO Min",
    "NPO Max",
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
      <Tabs
        sx={{ width: 1 }}
        value={value}
        onChange={handleChange}
        aria-label="basic tabs example"
      >
        <Tab label={t("study.modelization.clusters.matrix.common")} />
        <Tab label={t("study.modelization.clusters.matrix.tsGen")} />
        <Tab label={t("study.modelization.clusters.matrix.timeSeries")} />
      </Tabs>
      <Box
        sx={{
          display: "flex",
          width: "100%",
          height: "100%",
        }}
      >
        {R.cond([
          [
            () => value === 0,
            () => (
              <MatrixInput
                study={study}
                url={`input/thermal/prepro/${areaId}/${clusterId}/modulation`}
                computStats={MatrixStats.NOCOL}
                title={t("study.modelization.clusters.matrix.common")}
                columnsNames={commonNames}
              />
            ),
          ],
          [
            () => value === 1,
            () => (
              <MatrixInput
                study={study}
                url={`input/thermal/prepro/${areaId}/${clusterId}/data`}
                computStats={MatrixStats.NOCOL}
                title={t("study.modelization.clusters.matrix.tsGen")}
                columnsNames={tsGenNames}
              />
            ),
          ],
          [
            R.T,
            () => (
              <MatrixInput
                study={study}
                url={`input/thermal/series/${areaId}/${clusterId}/series`}
                computStats={MatrixStats.NOCOL}
                title={t("study.modelization.clusters.matrix.timeSeries")}
              />
            ),
          ],
        ])()}
      </Box>
    </Box>
  );
}

export default Matrix;
