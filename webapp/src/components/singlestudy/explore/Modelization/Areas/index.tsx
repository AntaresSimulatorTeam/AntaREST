/* eslint-disable react-hooks/exhaustive-deps */
import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useState } from "react";
import { useOutletContext } from "react-router";
import { Area, StudyMetadata } from "../../../../../common/types";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../common/page/NoContent";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";
import useSynthesis from "./useSynthesis";

function Areas() {
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  // const [areas, setAreas] = useState<Array<Area>>([]);
  const [selectedArea, setSelectedArea] = useState<Area>();
  const {
    value: areas,
    error,
    isLoading,
  } = useSynthesis({
    studyId: study ? study.id : "",
    selector: (state) => state.areas,
  });

  const handleAreaClick = (areaName: string): void => {
    console.log(areaName);
    if (areas === undefined) return;
    const elm = areas[areaName];
    if (elm) setSelectedArea(elm);
    // Put selected area on Redux
  };
  console.log("HEY AREAS: ", { areas, error, isLoading });
  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          <AreaPropsView
            areas={[]}
            onClick={handleAreaClick}
            currentArea={
              selectedArea !== undefined ? selectedArea.name : undefined
            }
          />
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
            () => selectedArea !== undefined && !isLoading,
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
