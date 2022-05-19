import { useEffect, useState, useCallback } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { getStudyData } from "../../../../../services/api/study";
import StudyTreeView from "./StudyTreeView";
import StudyDataView from "./StudyDataView";
import { StudyDataType, StudyMetadata } from "../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { scrollbarStyle } from "../../../../../theme";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";

const logError = debug("antares:studyview:error");

interface ElementView {
  type: StudyDataType;
  data: string;
}

function DebugView() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [studyData, setStudyData] = useState<any>();
  const [loaded, setLoaded] = useState(false);
  const [elementView, setElementView] = useState<ElementView>();

  const initStudyData = useCallback(
    async (sid: string) => {
      setLoaded(false);
      try {
        const data = await getStudyData(sid, "", -1);
        setStudyData(data);
      } catch (e) {
        enqueueErrorSnackbar(
          t("global:studies.error.retrieveData"),
          e as AxiosError
        );
        logError("Failed to fetch study data", sid, e);
      } finally {
        setLoaded(true);
      }
    },
    [enqueueErrorSnackbar, t]
  );

  useEffect(() => {
    if (study && !study.archived) {
      initStudyData(study.id);
    }
  }, [study, initStudyData]);

  return (
    <Box
      flex={1}
      width="100%"
      display="flex"
      flexDirection="row"
      justifyContent="flex-start"
      alignItems="center"
      overflow="hidden"
      boxSizing="border-box"
    >
      {study && studyData && (
        <>
          <Box
            height="100%"
            flex="0 0 30%"
            overflow="auto"
            sx={{ ...scrollbarStyle }}
          >
            <Box p={1}>
              {studyData && (
                <StudyTreeView
                  data={studyData}
                  view={(type, data) => setElementView({ type, data })}
                />
              )}
            </Box>
          </Box>
          <Box
            flex={1}
            height="100%"
            overflow="hidden"
            display="flex"
            boxSizing="border-box"
          >
            <Box px={2} flexGrow={1} overflow="hidden" display="flex">
              {elementView && (
                <StudyDataView
                  study={study.id}
                  studyData={studyData}
                  setStudyData={setStudyData}
                  type={elementView.type}
                  data={elementView.data}
                />
              )}
            </Box>
          </Box>
        </>
      )}
      {!loaded && studyData === undefined && <SimpleLoader />}
    </Box>
  );
}

export default DebugView;
