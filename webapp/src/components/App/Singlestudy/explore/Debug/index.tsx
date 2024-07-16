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
import type { FileInfo, TreeFolder } from "./utils";
import * as R from "ramda";
import SplitView from "../../../../common/SplitView";

function Debug() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [selectedFile, setSelectedFile] = useState<FileInfo>();

  const res = usePromiseWithSnackbarError(
    async () => {
      const treeData = await getStudyData<TreeFolder>(study.id, "", -1);
      return R.omit(["Desktop", "study", "logs"], treeData);
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
    <SplitView id="debug" sizes={[15, 85]}>
      <Box sx={{ overflow: "auto" }}>
        <UsePromiseCond
          response={res}
          ifResolved={(data) => (
            <DebugContext.Provider value={contextValue}>
              <Tree data={data} />
            </DebugContext.Provider>
          )}
        />
      </Box>
      <Box>{selectedFile && <Data {...selectedFile} studyId={study.id} />}</Box>
    </SplitView>
  );
}

export default Debug;
