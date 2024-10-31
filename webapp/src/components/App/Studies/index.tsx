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

import { useState } from "react";
import { useTranslation } from "react-i18next";

import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { Box, Divider } from "@mui/material";

import SimpleLoader from "@/components/common/loaders/SimpleLoader";
import RootPage from "@/components/common/page/RootPage";
import UseAsyncAppSelectorCond from "@/redux/components/UseAsyncAppSelectorCond";
import { fetchStudies } from "@/redux/ducks/studies";
import useAsyncAppSelector from "@/redux/hooks/useAsyncAppSelector";
import {
  getStudiesState,
  getStudyIdsFilteredAndSorted,
} from "@/redux/selectors";

import FilterDrawer from "./FilterDrawer";
import HeaderBottom from "./HeaderBottom";
import HeaderTopRight from "./HeaderTopRight";
import RefreshButton from "./RefreshButton";
import SideNav from "./SideNav";
import StudiesList from "./StudiesList";

function Studies() {
  const [t] = useTranslation();
  const res = useAsyncAppSelector({
    entityStateSelector: getStudiesState,
    fetchAction: fetchStudies,
    valueSelector: getStudyIdsFilteredAndSorted,
  });
  const [openFilter, setOpenFilter] = useState(false);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage
      title={t("global.studies")}
      titleIcon={TravelExploreOutlinedIcon}
      headerTopRight={<HeaderTopRight />}
      headerBottom={
        <HeaderBottom onOpenFilterClick={() => setOpenFilter(true)} />
      }
    >
      <Box
        sx={{
          flex: 1,
          width: 1,
          display: "flex",
          flexDirection: "row",
          justifyContent: "flex-start",
          alignItems: "flex-start",
          boxSizing: "border-box",
        }}
      >
        <SideNav />
        <Divider sx={{ width: "1px", height: "98%", bgcolor: "divider" }} />
        <UseAsyncAppSelectorCond
          response={res}
          ifLoading={() => <SimpleLoader />}
          ifFailed={() => (
            <Box
              sx={{
                width: 1,
                height: 1,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <RefreshButton showLabel />
            </Box>
          )}
          ifSucceeded={(value) => <StudiesList studyIds={value} />}
        />
        <FilterDrawer open={openFilter} onClose={() => setOpenFilter(false)} />
      </Box>
    </RootPage>
  );
}

export default Studies;
