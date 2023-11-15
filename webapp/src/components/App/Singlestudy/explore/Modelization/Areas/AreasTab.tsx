/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Paper } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../common/types";
import TabWrapper from "../../TabWrapper";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";

interface Props {
  renewablesClustering: boolean;
}

function AreasTab(props: Props) {
  const { renewablesClustering } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();

  const tabList = useMemo(() => {
    const baseTabs = [
      {
        label: t("study.modelization.properties"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/properties`,
      },
      {
        label: t("study.modelization.load"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/load`,
      },
      {
        label: t("study.modelization.thermal"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/thermal`,
      },
      {
        label: t("study.modelization.storages"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/storages`,
      },
      {
        label: t("study.modelization.hydro"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/hydro`,
      },
      {
        label: t("study.modelization.wind"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/wind`,
      },
      {
        label: t("study.modelization.solar"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/solar`,
      },
      {
        label: t("study.modelization.reserves"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/reserves`,
      },
      {
        label: t("study.modelization.miscGen"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/miscGen`,
      },
    ];
    if (renewablesClustering) {
      baseTabs.splice(4, 2, {
        label: t("study.modelization.renewables"),
        path: `/studies/${study.id}/explore/modelization/area/${areaId}/renewables`,
      });
    }
    return baseTabs;
  }, [study.id, areaId, renewablesClustering]);

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
