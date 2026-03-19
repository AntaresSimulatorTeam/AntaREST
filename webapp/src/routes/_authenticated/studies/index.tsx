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

import FolderIcon from "@mui/icons-material/Folder";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import SimpleLoader from "@/components/loaders/SimpleLoader";
import RootPage from "@/components/page/RootPage";
import SplitView from "@/components/page/SplitView";
import ViewWrapper from "@/components/page/ViewWrapper";
import { directoryQueries } from "@/queries/directories/queries";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesStatus, getStudyIdsFilteredAndSorted } from "@/redux/selectors";
import { FetchStatus } from "@/redux/utils";
import FiltersDrawer from "./-components/FiltersDrawer";
import HeaderActions from "./-components/HeaderActions";
import RefreshButton from "./-components/RefreshButton";
import StudiesList from "./-components/StudiesList";
import StudyTree from "./-components/StudyTree";

export const Route = createFileRoute("/_authenticated/studies/")({
  component: Studies,
  loader: async ({ context }) => {
    await context.queryClient.ensureQueryData(directoryQueries.list());
  },
});

function Studies() {
  const [openFilter, setOpenFilter] = useState(false);
  const { t } = useTranslation();
  const studiesStatus = useAppSelector(getStudiesStatus);
  const studyIds = useAppSelector(getStudyIdsFilteredAndSorted);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage
      title={t("global.studies")}
      titleIcon={FolderIcon}
      headerActions={<HeaderActions onOpenFilterClick={() => setOpenFilter(true)} />}
    >
      <SplitView splitId="studies" minSize={[300, 800]}>
        {/* Left - Studies tree explorer */}
        <StudyTree />

        {/* Right - Studies list */}
        <ViewWrapper flex disablePadding>
          {(studiesStatus === FetchStatus.Loading || studiesStatus === FetchStatus.Idle) && (
            <SimpleLoader />
          )}
          {studiesStatus === FetchStatus.Failed && (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <RefreshButton />
            </Box>
          )}
          {studiesStatus === FetchStatus.Succeeded && <StudiesList studyIds={studyIds} />}
        </ViewWrapper>
      </SplitView>
      <FiltersDrawer open={openFilter} onClose={() => setOpenFilter(false)} />
    </RootPage>
  );
}
