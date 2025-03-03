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

import { useState } from "react";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import SideNav from "./SideNav";
import StudiesList from "./StudiesList";
import { fetchStudies } from "@/redux/ducks/studies";
import RootPage from "../../common/page/RootPage";
import HeaderActions from "./HeaderActions";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import { getStudiesState, getStudyIdsFilteredAndSorted } from "@/redux/selectors";
import useAsyncAppSelector from "../../../redux/hooks/useAsyncAppSelector";
import FilterDrawer from "./FilterDrawer";
import UseAsyncAppSelectorCond from "../../../redux/components/UseAsyncAppSelectorCond";
import RefreshButton from "./RefreshButton";
import SplitView from "@/components/common/SplitView";
import ViewWrapper from "@/components/common/page/ViewWrapper";

function Studies() {
  const res = useAsyncAppSelector({
    entityStateSelector: getStudiesState,
    fetchAction: fetchStudies,
    valueSelector: getStudyIdsFilteredAndSorted,
  });

  const [openFilter, setOpenFilter] = useState(false);
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage
      title={t("global.studies")}
      titleIcon={TravelExploreOutlinedIcon}
      headerActions={<HeaderActions onOpenFilterClick={() => setOpenFilter(true)} />}
    >
      <SplitView id="studies" direction="horizontal" sizes={[30, 70]}>
        {/* Left */}
        <SideNav />
        {/* Right */}
        <ViewWrapper flex disablePadding>
          <UseAsyncAppSelectorCond
            response={res}
            ifLoading={() => <SimpleLoader />}
            ifSucceeded={(studyIds) => <StudiesList studyIds={studyIds} />}
            ifFailed={() => (
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
          />
        </ViewWrapper>
      </SplitView>
      <FilterDrawer open={openFilter} onClose={() => setOpenFilter(false)} />
    </RootPage>
  );
}

export default Studies;
