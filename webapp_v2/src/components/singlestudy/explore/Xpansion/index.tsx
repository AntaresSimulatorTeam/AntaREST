/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../common/types";
import TabWrapper from "../TabWrapper";

function Xpansion() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  const tabList = useMemo(
    () => [
      {
        label: t("xpansion:candidates"),
        path: `/studies/${study?.id}/explore/xpansion/candidates`,
      },
      {
        label: t("main:settings"),
        path: `/studies/${study?.id}/explore/xpansion/settings`,
      },
      {
        label: t("main:files"),
        path: `/studies/${study?.id}/explore/xpansion/files`,
      },
      {
        label: t("xpansion:capacities"),
        path: `/studies/${study?.id}/explore/xpansion/capacities`,
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

export default Xpansion;
