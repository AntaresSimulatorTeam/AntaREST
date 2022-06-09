import { memo } from "react";
import { Box, Skeleton } from "@mui/material";
import { GridChildComponentProps, areEqual } from "react-window";
import { StudyMetadata } from "../../../common/types";
import StudyCard from "../StudyCard";
import { StudiesListProps } from ".";

type Props = GridChildComponentProps<{
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
  columnCount: number;
  columnWidth: number;
  rowHeight: number;
  studyIds: StudiesListProps["studyIds"];
  selectedStudies: Array<string>;
  toggleSelect: (sid: string) => void;
  selectionMode: boolean;
}>;

const StudyCardCell = memo<Props>(
  (props) => {
    const { columnIndex, rowIndex, style, isScrolling, data } = props;
    const {
      setStudyToLaunch,
      columnCount,
      columnWidth,
      rowHeight,
      studyIds,
      selectedStudies,
      toggleSelect,
      selectionMode,
    } = data;
    const width = columnWidth - 10;
    const height = rowHeight - 10;
    const studyId = studyIds[columnIndex + rowIndex * columnCount];

    return (
      <Box
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          ...style,
        }}
      >
        {isScrolling ? (
          <Skeleton variant="rectangular" width={width} height={height} />
        ) : (
          <StudyCard
            id={studyId}
            setStudyToLaunch={setStudyToLaunch}
            width={width}
            height={height}
            selectionMode={selectionMode}
            selected={
              selectedStudies.indexOf(studyId) !== -1
            }
            toggleSelect={toggleSelect}
          />
        )}
      </Box>
    );
  },
  (prevProps, nextProps) => {
    // Prevents re-render of visible cells on scrolling
    const { isScrolling: prevIsScrolling, selectedStudies: prevSelectedStudies, ...prevRest } = prevProps;
    const { isScrolling: nextIsScrolling, selectedStudies: nextSelectedStudies, ...nextRest } = nextProps;
    const hasSelectionChanged = 
    return (
      !!(nextIsScrolling === prevIsScrolling || nextIsScrolling) &&
      areEqual(prevRest, nextRest)
    );
  }
);

export default StudyCardCell;
