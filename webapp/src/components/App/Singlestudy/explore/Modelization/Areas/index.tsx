import { Box } from "@mui/material";
import * as R from "ramda";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../common/page/SimpleContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import {
  getStudySynthesis,
  getCurrentArea,
} from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentArea } from "../../../../../../redux/ducks/studySyntheses";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";

function Areas() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { isLoading, error } = useStudySynthesis({ studyId: study.id });
  const currentArea = useAppSelector(getCurrentArea);
  const renewablesClustering = useAppSelector(
    (state) => getStudySynthesis(state, study.id)?.enr_modelling
  );
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaClick = (areaId: string): void => {
    dispatch(setCurrentArea(areaId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          <AreaPropsView
            studyId={study.id}
            onClick={handleAreaClick}
            currentArea={currentArea?.id}
          />
        </Box>
      }
      right={
        <>
          {R.cond([
            // Loading
            [() => isLoading, () => <SimpleLoader />],
            // Error
            [
              () => error !== undefined,
              () => <SimpleContent title={error?.message} />,
            ],
            // Area list
            [
              () => !!currentArea,
              () => (
                <AreasTab
                  renewablesClustering={renewablesClustering !== "aggregated"}
                />
              ),
            ],
            // No Areas
            [R.T, () => <SimpleContent title="No areas" />],
          ])()}
        </>
      }
    />
  );
}

export default Areas;
