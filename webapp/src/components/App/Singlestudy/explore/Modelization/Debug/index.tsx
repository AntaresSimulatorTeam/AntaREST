import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import Tree from "./Tree";
import Data from "./Data";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import SimpleContent from "../../../../../common/page/SimpleContent";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { getStudyData } from "../../../../../../services/api/study";
import DebugContext from "./DebugContext";
import { TreeData, filterTreeData, File } from "./utils";

function Debug() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [selectedFile, setSelectedFile] = useState<File>();

  const studyTree = usePromiseWithSnackbarError(
    async () => {
      const treeData = await getStudyData<TreeData>(study.id, "", -1);
      return filterTreeData(treeData);
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id],
    },
  );

  const handleFileSelection = useCallback(
    (fileType: File["fileType"], filePath: string) => {
      setSelectedFile({ fileType, filePath });
    },
    [],
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const contextValue = useMemo(
    () => ({
      treeData: studyTree.data ?? {},
      onFileSelect: handleFileSelection,
      reloadTreeData: studyTree.reload,
    }),
    [studyTree.data, studyTree.reload, handleFileSelection],
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
          response={studyTree}
          ifPending={() => <SimpleLoader />}
          ifResolved={() => (
            <>
              <Box sx={{ height: 1, flex: "0 0 20%", overflow: "auto" }}>
                <Tree />
              </Box>
              <Box sx={{ height: 1, flex: 1, overflow: "auto" }}>
                {selectedFile && (
                  <Data
                    studyId={study.id}
                    fileType={selectedFile.fileType}
                    filePath={selectedFile.filePath}
                  />
                )}
              </Box>
            </>
          )}
          ifRejected={(error) => <SimpleContent title={error?.toString()} />}
        />
      </Box>
    </DebugContext.Provider>
  );
}

export default Debug;
