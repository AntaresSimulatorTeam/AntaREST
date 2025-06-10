/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { setStudyScrollPosition } from "@/redux/ducks/studies";
import { getStudiesScrollPosition } from "@/redux/selectors";
import type { StudyMetadata } from "@/types/types";
import { Box } from "@mui/material";
import { useCallback, useState } from "react";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeGrid, type GridOnScrollProps } from "react-window";
import useDebounce from "../../../../hooks/useDebounce";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import LauncherDialog from "../../shared/studies/dialogs/LauncherDialog";
import Header from "./Header";
import StudyCardCell, { type StudyCardCellProps } from "./StudyCardCell";

const CARD_TARGET_WIDTH = 500;
const CARD_HEIGHT = 250;

export interface StudiesListProps {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudiesList({ studyIds }: StudiesListProps) {
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const [studiesToLaunch, setStudiesToLaunch] = useState<Array<StudyMetadata["id"]>>([]);
  const [selectedStudyIds, setSelectedStudyIds] = useState<Array<StudyMetadata["id"]>>([]);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Actions
  ////////////////////////////////////////////////////////////////

  const toggleStudySelection = useCallback((studyId: StudyMetadata["id"]) => {
    setSelectedStudyIds((prev) =>
      prev.includes(studyId) ? prev.filter((id) => id !== studyId) : [...prev, studyId],
    );
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScroll = useDebounce(
    (scrollProp: GridOnScrollProps) => {
      dispatch(setStudyScrollPosition(scrollProp.scrollTop));
    },
    { wait: 400, trailing: true },
  );

  const handleLauncherClose = () => {
    setStudiesToLaunch([]);
    setSelectedStudyIds([]);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Header
        studyIds={studyIds}
        selectedStudyIds={selectedStudyIds}
        setSelectedStudyIds={setSelectedStudyIds}
        setStudiesToLaunch={setStudiesToLaunch}
      />
      {/* <StudiesPreview /> */}
      <Box sx={{ flex: 1, pl: 1, pb: 1, overflowX: "hidden" }}>
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 10;
            const columnWidth =
              paddedWidth / Math.max(Math.floor(paddedWidth / CARD_TARGET_WIDTH), 1);
            const columnCount = Math.floor(paddedWidth / columnWidth);
            const rowHeight = CARD_HEIGHT;

            return (
              <FixedSizeGrid
                key={studyIds.join()}
                columnCount={columnCount}
                columnWidth={columnWidth}
                height={height}
                width={width}
                rowCount={Math.ceil(studyIds.length / columnCount)}
                rowHeight={rowHeight}
                initialScrollTop={scrollPosition}
                onScroll={handleScroll}
                useIsScrolling
                itemData={
                  {
                    studyIds,
                    columnCount,
                    columnWidth,
                    rowHeight,
                    selectedStudyIds,
                    toggleStudySelection,
                  } satisfies StudyCardCellProps["data"]
                }
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {studiesToLaunch.length > 0 && (
        <LauncherDialog open studyIds={studiesToLaunch} onClose={handleLauncherClose} />
      )}
    </>
  );
}

export default StudiesList;
