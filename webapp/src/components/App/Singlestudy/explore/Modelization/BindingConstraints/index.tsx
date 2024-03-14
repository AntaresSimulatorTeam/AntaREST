import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../common/page/SimpleContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import BindingConstPropsView from "./BindingConstPropsView";
import {
  getBindingConst,
  getCurrentBindingConstId,
} from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studySyntheses";
import BindingConstView from "./BindingConstView";
import usePromise from "../../../../../../hooks/usePromise";
import { getBindingConstraintList } from "../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  const currentConstraintId = useAppSelector(getCurrentBindingConstId);

  const bindingConstraints = useAppSelector((state) =>
    getBindingConst(state, study.id),
  );

  // TODO find better name
  const constraints = usePromise(
    () => getBindingConstraintList(study.id),
    [study.id, bindingConstraints],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConstraintChange = (bindingConstId: string): void => {
    dispatch(setCurrentBindingConst(bindingConstId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // TODO use Split + Refactor logic to be simpler and select the first contraint by default
  return (
    <SplitLayoutView
      left={
        <UsePromiseCond
          response={constraints}
          ifPending={() => <SimpleLoader />}
          ifResolved={(data) => (
            <Box width="100%" height="100%">
              <BindingConstPropsView
                onClick={handleConstraintChange}
                list={data || []}
                studyId={study.id}
                currentBindingConst={currentConstraintId || undefined}
              />
            </Box>
          )}
        />
      }
      right={
        <>
          {R.cond([
            // Binding constraints list
            [
              () => !!currentConstraintId && constraints.data !== undefined,
              () =>
                (
                  <BindingConstView constraintId={currentConstraintId} />
                ) as ReactNode,
            ],
            // No Areas
            [
              R.T,
              () =>
                (<SimpleContent title="No Binding Constraints" />) as ReactNode,
            ],
          ])()}
        </>
      }
    />
  );
}

export default BindingConstraints;
