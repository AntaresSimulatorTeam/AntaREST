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
import {
  getFileType,
  type TreeData,
  type FileInfo,
  type TreeFolder,
} from "./utils";
import * as R from "ramda";
import SplitView from "../../../../common/SplitView";
import { useUpdateEffect } from "react-use";

function Debug() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);

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
      setSelectedFile,
      reloadTreeData: res.reload,
    }),
    [res.reload],
  );

  useUpdateEffect(() => {
    const firstChildName = Object.keys(res.data ?? {})[0];
    const treeData = R.path<TreeData>([firstChildName], res.data);

    if (treeData) {
      const fileInfo = {
        fileType: getFileType(treeData),
        filename: firstChildName,
        filePath: firstChildName,
        treeData,
      };

      setSelectedFile(fileInfo);
    } else {
      setSelectedFile(null);
    }
  }, [res?.data]);

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
              <Tree
                data={data}
                selectedItemId={selectedFile?.filePath || null}
              />
            </DebugContext.Provider>
          )}
        />
      </Box>
      <Box>
        {selectedFile && (
          <Data
            {...selectedFile}
            setSelectedFile={setSelectedFile}
            studyId={study.id}
          />
        )}
      </Box>
    </SplitView>
  );
}

export default Debug;
