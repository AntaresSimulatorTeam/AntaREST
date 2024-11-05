/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { memo } from "react";
import { areEqual, GridChildComponentProps } from "react-window";

import { Box, Skeleton } from "@mui/material";

import { StudyMetadata } from "@/common/types";

import StudyCard from "../StudyCard";

import { StudiesListProps } from ".";

type Props = GridChildComponentProps<{
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
  columnCount: number;
  columnWidth: number;
  rowHeight: number;
  studyIds: StudiesListProps["studyIds"];
  selectedStudies: string[];
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
            selected={selectedStudies.indexOf(studyId) !== -1}
            toggleSelect={toggleSelect}
          />
        )}
      </Box>
    );
  },
  (prevProps, nextProps) => {
    // Prevents re-render of visible cells on scrolling
    const { isScrolling: prevIsScrolling, ...prevRest } = prevProps;
    const { isScrolling: nextIsScrolling, ...nextRest } = nextProps;
    return (
      !!(nextIsScrolling === prevIsScrolling || nextIsScrolling) &&
      areEqual(prevRest, nextRest)
    );
  },
);

StudyCardCell.displayName = "StudyCardCell";

export default StudyCardCell;
