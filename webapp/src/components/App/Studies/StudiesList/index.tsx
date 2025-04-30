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

import { useCallback, useState } from "react";
import { Box } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeGrid, type GridOnScrollProps } from "react-window";
import type { StudyMetadata } from "@/types/types";
import { setStudyScrollPosition } from "@/redux/ducks/studies";
import LauncherDialog from "../LauncherDialog";
import useDebounce from "../../../../hooks/useDebounce";
import { getStudiesScrollPosition } from "@/redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import StudyCardCell from "./StudyCardCell";
import Header from "./Header";

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

  const setStudyToLaunch = useCallback((studyId: StudyMetadata["id"]) => {
    setStudiesToLaunch([studyId]);
  }, []);

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
                itemData={{
                  studyIds,
                  setStudyToLaunch,
                  columnCount,
                  columnWidth,
                  rowHeight,
                  selectedStudyIds,
                  toggleStudySelection,
                }}
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
