/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { directoryQueries } from "@/queries/directories/queries";
import { setStudyScrollPosition } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesScrollPosition } from "@/redux/selectors";
import type { StudyMetadata } from "@/types/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Box } from "@mui/material";
import { useCallback, useState } from "react";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeGrid, type GridOnScrollProps } from "react-window";
import useDebounce from "@/hooks/useDebounce";
import StudyLaunchDialog from "../../../../-shared/components/studies/dialogs/StudyLaunchDialog";
import Header from "./Header";
import StudyCardCell from "./StudyCardCell";
import type { StudyCellData } from "./StudyCardCell/types";
import type { ViewMode } from "./types";

const CARD_TARGET_WIDTH = 380;
const CARD_HEIGHT = 130;
const LIST_ROW_HEIGHT = 76;

export interface StudiesListProps {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudiesList({ studyIds }: StudiesListProps) {
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const [studiesToLaunch, setStudiesToLaunch] = useState<Array<StudyMetadata["id"]>>([]);
  const [selectedStudyIds, setSelectedStudyIds] = useState<Array<StudyMetadata["id"]>>([]);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const dispatch = useAppDispatch();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

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
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />
      <Box sx={{ flex: 1, pl: 1, pb: 1, overflowX: "hidden" }}>
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 10;
            const columnCount =
              viewMode === "list" ? 1 : Math.max(Math.floor(paddedWidth / CARD_TARGET_WIDTH), 1);
            const columnWidth = viewMode === "list" ? paddedWidth : paddedWidth / columnCount;
            const rowHeight = viewMode === "list" ? LIST_ROW_HEIGHT : CARD_HEIGHT;

            return (
              <FixedSizeGrid
                key={`${viewMode}-${studyIds.join()}`}
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
                    viewMode,
                    directories,
                  } satisfies StudyCellData
                }
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {studiesToLaunch.length > 0 && (
        <StudyLaunchDialog open studyIds={studiesToLaunch} onClose={handleLauncherClose} />
      )}
    </>
  );
}

export default StudiesList;
