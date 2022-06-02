/* eslint-disable react-hooks/exhaustive-deps */
import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useMemo } from "react";
import { useOutletContext } from "react-router";
import { PayloadAction } from "@reduxjs/toolkit";
import {
  FileStudyTreeConfigDTO,
  StudyMetadata,
} from "../../../../../common/types";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../common/page/NoContent";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import CustomPropsView from "./CustomPropsView";
import CustomTab from "./CustomTab";
import useStudyData from "../../hooks/useStudyData";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import { AppState } from "../../../../../redux/ducks";

interface Props<T> {
  selector: (state: FileStudyTreeConfigDTO) => T;
  getCurrentElement: (state: AppState) => string;
  setCurrentElement: (payload: string) => PayloadAction;
  noContentMessage: string;
  tabList: Array<{
    label: string;
    path: string;
  }>;
}

function CommonElement<T>(props: Props<T>) {
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const {
    selector,
    getCurrentElement,
    setCurrentElement,
    tabList,
    noContentMessage,
  } = props;
  const { value, error, isLoading } = useStudyData({
    studyId: study ? study.id : "",
    selector,
  });
  const currentElement = useAppSelector(getCurrentElement);
  const dispatch = useAppDispatch();
  const selectedElement = useMemo(() => {
    if (value !== undefined && currentElement) {
      return (value as any)[currentElement];
    }
    return undefined;
  }, [currentElement, value]);

  const handleAreaClick = (element: string): void => {
    if (value === undefined) return;
    const elm = (value as any)[element.toLowerCase()];
    if (elm) {
      dispatch(setCurrentElement(element.toLowerCase()));
    }
  };

  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          {value !== undefined && !isLoading && (
            <CustomPropsView
              element={Object.keys(value).map((item) => (value as any)[item])}
              onClick={handleAreaClick}
              currentElement={
                selectedElement !== undefined ? selectedElement.name : undefined
              }
            />
          )}
        </Box>
      }
      right={
        R.cond([
          // Loading
          [
            () => selectedElement !== undefined && isLoading,
            () => (<SimpleLoader />) as ReactNode,
          ],
          // Area list
          [
            () =>
              selectedElement !== undefined &&
              !isLoading &&
              (!error || error === undefined),
            () => (<CustomTab tabList={tabList} />) as ReactNode,
          ],
          // No Areas
          [R.T, () => (<NoContent title={noContentMessage} />) as ReactNode],
        ])() as ReactNode
      }
    />
  );
}

export default CommonElement;
