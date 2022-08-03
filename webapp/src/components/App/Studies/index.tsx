import { useState } from "react";
import { Box, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import SideNav from "./SideNav";
import StudiesList from "./StudiesList";
import { fetchStudies } from "../../../redux/ducks/studies";
import RootPage from "../../common/page/RootPage";
import HeaderTopRight from "./HeaderTopRight";
import HeaderBottom from "./HeaderBottom";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import {
  getStudiesState,
  getStudyIdsFilteredAndSorted,
} from "../../../redux/selectors";
import useAsyncAppSelector from "../../../redux/hooks/useAsyncAppSelector";
import FilterDrawer from "./FilterDrawer";
import UseAsyncAppSelectorCond from "../../../redux/components/UseAsyncAppSelectorCond";
import RefreshButton from "./RefreshButton";

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
