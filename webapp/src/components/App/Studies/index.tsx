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

import SplitView from "@/components/common/SplitView";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import { getStudiesStatus, getStudyIdsFilteredAndSorted } from "@/redux/selectors";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import RootPage from "../../common/page/RootPage";
import FiltersDrawer from "./FiltersDrawer";
import HeaderActions from "./HeaderActions";
import SideNav from "./SideNav";
import StudiesList from "./StudiesList";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { FetchStatus } from "@/redux/utils";
import SimpleLoader from "@/components/common/loaders/SimpleLoader";
import RefreshButton from "./RefreshButton";
import { Box } from "@mui/material";

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
      titleIcon={TravelExploreOutlinedIcon}
      headerActions={<HeaderActions onOpenFilterClick={() => setOpenFilter(true)} />}
    >
      <SplitView splitId="studies" minSize={[200, 400]}>
        {/* Left */}
        <SideNav />
        {/* Right */}
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

export default Studies;
