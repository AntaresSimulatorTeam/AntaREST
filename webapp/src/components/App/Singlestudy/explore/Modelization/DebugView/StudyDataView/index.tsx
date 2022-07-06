/* eslint-disable @typescript-eslint/no-explicit-any */
import { CSSProperties, ReactNode } from "react";
import { Box } from "@mui/material";
import StudyFileView from "./StudyFileView";
import StudyJsonView from "./StudyJsonView";
import StudyMatrixView from "./StudyMatrixView/StudyMatrixView";
import { StudyDataType } from "../../../../../../../common/types";

interface PropTypes {
  study: string;
  type: StudyDataType;
  data: string;
  studyData: any;
  setStudyData: (elm: any) => void;
}

interface RenderData {
  css: CSSProperties;
  data: ReactNode;
}

function StudyDataView(props: PropTypes) {
  const { study, type, data, studyData, setStudyData } = props;
  const filterOut = ["output", "logs", "Desktop"];

  const refreshView = () => {
    setStudyData({ ...studyData });
  };

  const renderData = (): RenderData => {
    if (type === "file") {
      return {
        css: { overflow: "auto" },
        data: (
          <StudyFileView
            study={study}
            url={data}
            filterOut={filterOut}
            refreshView={refreshView}
          />
        ),
      };
    }
    if (type === "matrix" || type === "matrixfile") {
      return {
        css: { overflow: "auto" },
        data: (
          <StudyMatrixView study={study} url={data} filterOut={filterOut} />
        ),
      };
    }
    return {
      css: { overflow: "hidden", paddingTop: "0px" },
      data: <StudyJsonView study={study} data={data} filterOut={filterOut} />,
    };
  };

  const rd = renderData();
  return (
    <Box flexGrow={1} px={1} sx={rd.css}>
      {rd.data}
    </Box>
  );
}

export default StudyDataView;
