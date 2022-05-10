/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../common/types";
import TabWrapper from "../TabWrapper";

function Modelization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  const tabList = useMemo(
    () => [
      {
        label: t("singlestudy:map"),
        path: `/studies/${study?.id}/explore/modelization/map`,
      },
      {
        label: t("singlestudy:areas"),
        path: `/studies/${study?.id}/explore/modelization/area`,
      },
      {
        label: t("singlestudy:links"),
        path: `/studies/${study?.id}/explore/modelization/links`,
      },
      {
        label: t("singlestudy:bindingconstraints"),
        path: `/studies/${study?.id}/explore/modelization/bindingcontraint`,
      },
      {
        label: t("singlestudy:debug"),
        path: `/studies/${study?.id}/explore/modelization/debug`,
      },
    ],
    [study]
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
