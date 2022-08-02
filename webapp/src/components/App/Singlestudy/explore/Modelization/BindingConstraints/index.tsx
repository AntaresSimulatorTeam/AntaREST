import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../../common/page/NoContent";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import BindingConstPropsView from "./BindingConstPropsView";
import {
  getBindingConst,
  getCurrentBindingConstId,
} from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studyDataSynthesis";
import BindingConstView from "./BindingConstView";
import usePromise from "../../../../../../hooks/usePromise";
import { getStudyData } from "../../../../../../services/api/study";
import { BindingConstType } from "./BindingConstView/utils";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const pathPrefix = `input/bindingconstraints/bindingconstraints`;
  const bindingConstInitList = useAppSelector((state) =>
    getBindingConst(study.id, state)
  );
  console.log("BINDING CONST: ", bindingConstInitList);
  const {
    data: tmpStudyData,
    isLoading,
    error,
  } = usePromise(() => getStudyData(study.id, pathPrefix, 3), [study.id]);
  const studyData = useMemo(() => {
    const data: Array<BindingConstType> = [];
    if (tmpStudyData) {
      for (let i = 0; i < Object.keys(tmpStudyData).length; i += 1) {
        data.push(tmpStudyData[i.toString()]);
      }
    }
    return data;
  }, [tmpStudyData]);
  const currentBindingConst = useAppSelector(getCurrentBindingConstId);
  const bcIndex = useMemo(() => {
    const data = studyData?.findIndex((elm) => elm.id === currentBindingConst);
    return data !== undefined && data >= 0 ? data : undefined;
  }, [studyData, currentBindingConst]);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleBindingConstClick = (bindingConstId: string): void => {
    if (studyData === undefined) return;
    const elm = studyData.find((item) => item.id === bindingConstId);
    if (elm) {
      dispatch(setCurrentBindingConst(bindingConstId));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          {studyData !== undefined && (
            <BindingConstPropsView
              onClick={handleBindingConstClick}
              list={studyData}
              studyId={study.id}
              currentBindingConst={currentBindingConst || undefined}
            />
          )}
        </Box>
      }
      right={
        <>
          {R.cond([
            // Loading
            [
              () => isLoading || studyData.length === 0,
              () => (<SimpleLoader />) as ReactNode,
            ],
            [
              () => error !== undefined,
              () =>
                (
                  <NoContent
                    title={
                      (error as Error).message
                        ? (error as Error).message
                        : (error as string)
                    }
                  />
                ) as ReactNode,
            ],
            // Binding constraints list
            [
              () => currentBindingConst !== undefined && bcIndex !== undefined,
              () =>
                (
                  <BindingConstView
                    bcIndex={bcIndex as number}
                    bindingConst={currentBindingConst}
                  />
                ) as ReactNode,
            ],
            // No Areas
            [
              R.T,
              () => (<NoContent title="No Binding Constraints" />) as ReactNode,
            ],
          ])()}
        </>
      }
    />
  );
}

export default BindingConstraints;
