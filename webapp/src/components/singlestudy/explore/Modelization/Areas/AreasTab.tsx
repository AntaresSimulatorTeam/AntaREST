/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Paper } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import TabWrapper from "../../TabWrapper";

function AreasTab() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const tabList = useMemo(
    () => [
      {
        label: t("study.modelization.properties"),
        path: `/studies/${study?.id}/explore/modelization/area/properties`,
      },
      {
        label: t("study.modelization.load"),
        path: `/studies/${study?.id}/explore/modelization/area/load`,
      },
      {
        label: t("study.modelization.thermal"),
        path: `/studies/${study?.id}/explore/modelization/area/thermal`,
      },
      {
        label: t("study.modelization.hydro"),
        path: `/studies/${study?.id}/explore/modelization/area/hydro`,
      },
      {
        label: t("study.modelization.wind"),
        path: `/studies/${study?.id}/explore/modelization/area/wind`,
      },
      {
        label: t("study.modelization.reserve"),
        path: `/studies/${study?.id}/explore/modelization/area/reserve`,
      },
      {
        label: t("study.modelization.miscGen"),
        path: `/studies/${study?.id}/explore/modelization/area/miscGen`,
      },
    ],
    [study]
  );

  return (
    <Paper
      sx={{
        width: "100%",
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
