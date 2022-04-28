/* eslint-disable react-hooks/exhaustive-deps */
import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { StudyMetadata } from "../../../../common/types";
import TabWrapper from "../TabWrapper";

function Modelization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(
    () => [
      { label: "Map", path: `/studies/${study?.id}/explore/modelization/map` },
      {
        label: "Area",
        path: `/studies/${study?.id}/explore/modelization/area`,
      },
      {
        label: "Links",
        path: `/studies/${study?.id}/explore/modelization/links`,
      },
      {
        label: "Binding contraint",
        path: `/studies/${study?.id}/explore/modelization/bindingcontraint`,
      },
      {
        label: "Debug",
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
