import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import TabWrapper from "../TabWrapper";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";

function Modelization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();

  const tabList = useMemo(
    () => [
      {
        label: t("study.modelization.map"),
        path: `/studies/${study?.id}/explore/modelization/map`,
      },
      {
        label: t("study.areas"),
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}`,
      },
      {
        label: t("study.links"),
        path: `/studies/${study?.id}/explore/modelization/links`,
      },
      {
        label: t("study.bindingconstraints"),
        path: `/studies/${study?.id}/explore/modelization/bindingcontraint`,
      },
      {
        label: t("study.debug"),
        path: `/studies/${study?.id}/explore/modelization/debug`,
      },
      {
        label: t("study.modelization.tableMode"),
        path: `/studies/${study?.id}/explore/modelization/tablemode`,
      },
    ],
    [areaId, study?.id, t],
  );

  return (
    <Box
      width="100%"
      flexGrow={1}
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
    </Box>
  );
}

export default Modelization;
