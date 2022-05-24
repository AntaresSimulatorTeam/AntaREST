/* eslint-disable react-hooks/exhaustive-deps */
import { Box } from "@mui/material";
import * as R from "ramda";
import { ReactNode, useEffect, useState } from "react";
import { useOutletContext } from "react-router";
import { Area, StudyMetadata } from "../../../../../common/types";
import usePromise from "../../../../../hooks/usePromise";
import { getStudySynthesis } from "../../../../../services/api/variant";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import NoContent from "../../../../common/page/NoContent";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";

function Areas() {
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const [areas, setAreas] = useState<Array<Area>>([]);
  const [selectedArea, setSelectedArea] = useState<Area>();
  const { data: synthesis, isLoading } = usePromise(
    async () => {
      console.log("HELLO");
      if (study?.id) {
        return getStudySynthesis(study?.id);
      }
      return undefined;
    },
    {},
    [study?.id]
  );

  useEffect(() => {
    if (synthesis) {
      const areaList = Object.keys(synthesis.areas).map(
        (elm) => synthesis.areas[elm]
      );
      setAreas(areaList);
      if (areaList.length > 0) setSelectedArea(areaList[0]);

      console.log("AREAS: ", synthesis.areas);
    }
  }, [synthesis?.areas]);
  return (
    <SplitLayoutView
      left={
        <Box width="100%" height="100%">
          <AreaPropsView />
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
