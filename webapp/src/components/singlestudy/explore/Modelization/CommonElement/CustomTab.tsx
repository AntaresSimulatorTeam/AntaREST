/* eslint-disable react-hooks/exhaustive-deps */
import { useOutletContext } from "react-router-dom";
import { Paper } from "@mui/material";
import { StudyMetadata } from "../../../../../common/types";
import TabWrapper from "../../TabWrapper";

interface Props {
  tabList: Array<{
    label: string;
    path: string;
  }>;
}

function CustomTab(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { tabList } = props;
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

export default CustomTab;
