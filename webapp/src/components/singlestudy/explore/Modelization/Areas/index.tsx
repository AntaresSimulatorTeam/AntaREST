/* eslint-disable react-hooks/exhaustive-deps */
import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../common/types";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../common/page/NoContent";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";
import useStudyData from "../../hooks/useStudyData";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import { setCurrentArea } from "../../../../../redux/ducks/studydata";

function Areas() {
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const {
    value: areas,
    error,
    isLoading,
  } = useStudyData({
    studyId: study ? study.id : "",
    selector: (state) => state.areas,
  });
  console.log({ areas, isLoading, error });
  const currentArea = useAppSelector(getCurrentAreaId);
  const dispatch = useAppDispatch();
  const selectedArea = useMemo(() => {
    if (areas !== undefined && currentArea) {
      return areas[currentArea];
    }
    return undefined;
  }, [currentArea, areas]);

  const handleAreaClick = (areaName: string): void => {
    if (areas === undefined) return;
    const elm = areas[areaName.toLowerCase()];
    if (elm) {
      dispatch(setCurrentArea(areaName.toLowerCase()));
    }
    // Put selected area on Redux
  };

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          {areas !== undefined && !isLoading && (
            <AreaPropsView
              areas={Object.keys(areas).map((item) => areas[item])}
              onClick={handleAreaClick}
              currentArea={
                selectedArea !== undefined ? selectedArea.name : undefined
              }
            />
          )}
        </Box>
      }
      right={
        R.cond([
          // Loading
          [
            () => selectedArea !== undefined && isLoading,
            () => (<SimpleLoader />) as ReactNode,
          ],
          // Area list
          [
            () =>
              selectedArea !== undefined &&
              !isLoading &&
              (!error || error === undefined),
            () => (<AreasTab />) as ReactNode,
          ],
          // No Areas
          [R.T, () => (<NoContent title="No areas" />) as ReactNode],
        ])() as ReactNode
      }
    />
  );
}

export default Areas;
