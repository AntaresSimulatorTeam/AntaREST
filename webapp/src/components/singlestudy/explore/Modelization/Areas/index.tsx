import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode } from "react";
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
import { setCurrentArea } from "../../../../../redux/ducks/studyDataSynthesis";

function Areas() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const {
    value: studyData,
    error,
    isLoading,
  } = useStudyData({
    studyId: study.id,
    selector: (state) => ({
      areas: state.areas,
      renewablesClustering: state.enr_modelling,
    }),
  });
  const currentArea = useAppSelector(getCurrentAreaId);
  const dispatch = useAppDispatch();
  const selectedArea =
    studyData?.areas && currentArea ? studyData?.areas[currentArea] : undefined;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaClick = (areaId: string): void => {
    if (studyData?.areas === undefined) return;
    const elm = studyData?.areas[areaId];
    if (elm) {
      dispatch(setCurrentArea(areaId));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          {studyData?.areas !== undefined && !isLoading && (
            <AreaPropsView
              studyId={study.id}
              onClick={handleAreaClick}
              currentArea={currentArea !== undefined ? currentArea : undefined}
            />
          )}
        </Box>
      }
      right={
        <>
          {R.cond([
            // Loading
            [() => isLoading, () => (<SimpleLoader />) as ReactNode],
            [
              () => error !== undefined,
              () => (<NoContent title={error?.message} />) as ReactNode,
            ],
            // Area list
            [
              () => selectedArea !== undefined,
              () =>
                (
                  <AreasTab
                    renewablesClustering={
                      studyData?.renewablesClustering !== "aggregated"
                    }
                  />
                ) as ReactNode,
            ],
            // No Areas
            [R.T, () => (<NoContent title="No areas" />) as ReactNode],
          ])()}
        </>
      }
    />
  );
}

export default Areas;
