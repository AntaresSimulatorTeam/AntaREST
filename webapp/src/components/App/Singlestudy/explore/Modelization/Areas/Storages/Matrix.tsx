import * as React from "react";
import * as R from "ramda";
import { styled } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { useTranslation } from "react-i18next";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Storage } from "./utils";
import SplitLayoutView from "../../../../../../common/SplitLayoutView";

export const StyledTab = styled(Tabs)({
  width: "98%",
  borderBottom: 1,
  borderColor: "divider",
});

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
      <StyledTab value={value} onChange={(_, v) => setValue(v)}>
        <Tab label={t("study.modelization.storages.capacities")} />
        <Tab label={t("study.modelization.storages.ruleCurves")} />
        <Tab label={t("study.modelization.storages.inflows")} />
      </StyledTab>
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
                    title={t("study.modelization.storages.chargeCapacity")}
                  />
                }
                right={
                  <MatrixInput
                    study={study}
                    url={`input/st-storage/series/${areaId}/${storageId}/pmax_withdrawal`}
                    computStats={MatrixStats.NOCOL}
                    title={t("study.modelization.storages.dischargeCapacity")}
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
