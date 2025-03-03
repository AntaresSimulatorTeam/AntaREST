/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { Box } from "@mui/material";
import Tree from "./Tree";
import Data from "./Data";
import type { StudyMetadata } from "../../../../../types/types";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import { getStudyData } from "../../../../../services/api/study";
import DebugContext from "./DebugContext";
import { getFileType, type TreeData, type FileInfo, type TreeFolder } from "./utils";
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
  const path = searchParams.get("path");

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

    const pathSegments = path?.split("/");
    const filename = pathSegments ? R.last(pathSegments) : null;
    const treeData = pathSegments ? R.path<TreeData>(pathSegments, res.data) : null;

    let fileInfo: FileInfo | null = null;

    if (path && filename && treeData) {
      fileInfo = {
        fileType: getFileType(treeData),
        treeData,
        filename,
        filePath: path,
      };
    } else if (firstChildTreeData) {
      fileInfo = {
        fileType: getFileType(firstChildTreeData),
        treeData: firstChildTreeData,
        filename: firstChildName,
        filePath: firstChildName,
      };
    }

    setSelectedFile(fileInfo);
  }, [res.data, path]);

  useUpdateEffect(() => {
    if (selectedFile?.filePath !== path) {
      setSearchParams({ path: selectedFile?.filePath || "" });
    }
  }, [selectedFile?.filePath]);

  // TODO: to remove after ANT-2217 solved
  useUpdateEffect(() => {
    contextValue.reloadTreeData();
  }, [study.archived]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="debug" sizes={[20, 80]}>
      <Box sx={{ minWidth: 150, p: 1, overflow: "auto" }}>
        <UsePromiseCond
          response={res}
          ifFulfilled={(data) => (
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
            study={study}
          />
        )}
      </Box>
    </SplitView>
  );
}

export default Debug;
