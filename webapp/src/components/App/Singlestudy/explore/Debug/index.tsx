import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext, useSearchParams } from "react-router-dom";
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
  // Allow to keep expanded items when the tree is reloaded with `reloadTreeData`
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const pathInUrl = searchParams.get("path");

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
    const firstChildTreeData = R.path<TreeData>([firstChildName], res.data);

    const pathInUrlParts = pathInUrl?.split("/");
    const urlPathTreeData = pathInUrlParts
      ? R.path<TreeData>(pathInUrlParts, res.data)
      : null;

    let fileInfo: FileInfo | null = null;

    if (urlPathTreeData) {
      fileInfo = {
        fileType: getFileType(urlPathTreeData),
        treeData: urlPathTreeData,
        filename: R.last(pathInUrlParts!)!,
        filePath: pathInUrl!,
      };
    } else if (firstChildTreeData) {
      fileInfo = {
        fileType: getFileType(firstChildTreeData),
        treeData: firstChildTreeData,
        filename: firstChildName,
        filePath: firstChildName,
      };
    }

    if (fileInfo) {
      setSelectedFile(fileInfo);
    } else {
      setSelectedFile(null);
    }
  }, [res.data, pathInUrl]);

  useUpdateEffect(() => {
    if (selectedFile?.filePath !== pathInUrl) {
      setSearchParams({ path: selectedFile?.filePath || "" });
    }
  }, [selectedFile?.filePath]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="debug" sizes={[15, 85]}>
      <Box sx={{ px: 1, overflow: "auto" }}>
        <UsePromiseCond
          response={res}
          ifResolved={(data) => (
            <DebugContext.Provider value={contextValue}>
              <Tree
                data={data}
                currentPath={selectedFile?.filePath || null}
                expandedItems={expandedItems}
                setExpandedItems={setExpandedItems}
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
            reloadTreeData={res.reload}
            studyId={study.id}
          />
        )}
      </Box>
    </SplitView>
  );
}

export default Debug;
