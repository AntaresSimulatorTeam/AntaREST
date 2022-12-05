import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
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
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function Areas() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const res = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudySynthesis(state, id)?.enr_modelling,
  });
  const currentArea = useAppSelector(getCurrentArea);
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
        <UsePromiseCond
          response={res}
          ifResolved={(renewablesClustering) =>
            currentArea ? (
              <AreasTab
                renewablesClustering={renewablesClustering !== "aggregated"}
              />
            ) : (
              <SimpleContent title="No areas" />
            )
          }
        />
      }
    />
  );
}

export default Areas;
