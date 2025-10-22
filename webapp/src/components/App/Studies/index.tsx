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

import SplitView from "@/components/common/SplitView";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import { fetchStudies } from "@/redux/ducks/studies";
import { getStudiesState, getStudyIdsFilteredAndSorted } from "@/redux/selectors";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { Box } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import UseAsyncAppSelectorCond from "../../../redux/components/UseAsyncAppSelectorCond";
import useAsyncAppSelector from "../../../redux/hooks/useAsyncAppSelector";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import RootPage from "../../common/page/RootPage";
import FiltersDrawer from "./FiltersDrawer";
import HeaderActions from "./HeaderActions";
import RefreshButton from "./RefreshButton";
import SideNav from "./SideNav";
import StudiesList from "./StudiesList";

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
      <SplitView splitId="studies" minSize={[200, 400]}>
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
      <FiltersDrawer open={openFilter} onClose={() => setOpenFilter(false)} />
    </RootPage>
  );
}

export default Studies;
