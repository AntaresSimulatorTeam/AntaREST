import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import Tree from "./Tree";
import Data from "./Data";
import { StudyMetadata } from "../../../../../common/types";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import { getStudyData } from "../../../../../services/api/study";
import DebugContext from "./DebugContext";
import { TreeData, filterTreeData, File } from "./utils";

function Debug() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [selectedFile, setSelectedFile] = useState<File>();

  const res = usePromiseWithSnackbarError(
    async () => {
      const treeData = await getStudyData<TreeData>(study.id, "", -1);
      return filterTreeData(treeData);
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id],
    },
  );

  const contextValue = useMemo(
    () => ({
      onFileSelect: setSelectedFile,
      reloadTreeData: res.reload,
    }),
    [res.reload],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DebugContext.Provider value={contextValue}>
      <Box
        sx={{
          flex: 1,
          width: 1,
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
          overflow: "auto",
        }}
      >
        <UsePromiseCond
          response={res}
          ifResolved={(data) => (
            <>
              <Box sx={{ height: 1, flex: "0 0 20%", overflow: "auto" }}>
                <Tree data={data} />
              </Box>
              <Box sx={{ height: 1, flex: 1, overflow: "auto" }}>
                {selectedFile && <Data {...selectedFile} studyId={study.id} />}
              </Box>
            </>
          )}
        />
      </Box>
    </DebugContext.Provider>
  );
}

export default Debug;
