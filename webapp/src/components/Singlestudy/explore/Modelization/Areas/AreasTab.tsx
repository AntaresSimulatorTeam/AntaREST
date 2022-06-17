/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Paper } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import TabWrapper from "../../TabWrapper";

interface Props {
  renewablesClustering: boolean;
}

function AreasTab(props: Props) {
  const { renewablesClustering } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  const tabList = useMemo(() => {
    const baseTabs = [
      {
        label: t("study.modelization.properties"),
        path: `/studies/${study.id}/explore/modelization/area/properties`,
      },
      {
        label: t("study.modelization.load"),
        path: `/studies/${study.id}/explore/modelization/area/load`,
      },
      {
        label: t("study.modelization.thermal"),
        path: `/studies/${study.id}/explore/modelization/area/thermal`,
      },
      {
        label: t("study.modelization.hydro"),
        path: `/studies/${study.id}/explore/modelization/area/hydro`,
      },
      {
        label: t("study.modelization.wind"),
        path: `/studies/${study.id}/explore/modelization/area/wind`,
      },
      {
        label: t("study.modelization.solar"),
        path: `/studies/${study.id}/explore/modelization/area/solar`,
      },
      {
        label: t("study.modelization.reserves"),
        path: `/studies/${study.id}/explore/modelization/area/reserves`,
      },
      {
        label: t("study.modelization.miscGen"),
        path: `/studies/${study.id}/explore/modelization/area/miscGen`,
      },
    ];
    if (renewablesClustering) {
      baseTabs.splice(4, 2, {
        label: t("study.modelization.renewables"),
        path: `/studies/${study.id}/explore/modelization/area/renewables`,
      });
    }
    return baseTabs;
  }, [study, renewablesClustering]);

  return (
    <Paper
      sx={{
        width: "100%",
        height: "100%",
        flexGrow: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <TabWrapper study={study} tabList={tabList} />
    </Paper>
  );
}

export default AreasTab;
