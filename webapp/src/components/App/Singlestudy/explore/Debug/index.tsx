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

import { Box, Skeleton } from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { useUpdateEffect } from "react-use";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import type { StudyMetadata } from "../../../../../types/types";
import SplitView from "../../../../common/SplitView";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import Data from "./Data";
import DebugContext from "./DebugContext";
import Tree from "./Tree";
import { getFileType, getTreeData, type FileInfo, type TreeData } from "./utils";

function Debug() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  // Allow to keep expanded items when the tree is reloaded with `reloadTree`
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const path = searchParams.get("path");

  const treeDataResponse = usePromiseWithSnackbarError(() => getTreeData(study.id), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [study.id],
  });

  const contextValue = useMemo(
    () => ({
      setSelectedFile,
      reloadTree: treeDataResponse.reload,
      isTreeLoading: treeDataResponse.isLoading,
    }),
    [treeDataResponse.reload, treeDataResponse.isLoading],
  );

  // Update the selected file
  useUpdateEffect(() => {
    // Select the file corresponding to the `path` URL parameter

    const pathSegments = path?.split("/");
    const filename = pathSegments ? R.last(pathSegments) : null;
    const treeData = pathSegments ? R.path<TreeData>(pathSegments, treeDataResponse.data) : null;

    if (path && filename && treeData) {
      setSelectedFile({
        fileType: getFileType(treeData),
        treeData,
        filename,
        filePath: path,
      });

      return;
    }

    // Select the first child of the tree data

    const firstChildName = Object.keys(treeDataResponse.data ?? {})[0];
    const firstChildTreeData = R.path<TreeData>([firstChildName], treeDataResponse.data);

    if (firstChildTreeData) {
      setSelectedFile({
        fileType: getFileType(firstChildTreeData),
        treeData: firstChildTreeData,
        filename: firstChildName,
        filePath: firstChildName,
      });

      return;
    }

    setSelectedFile(null);
  }, [treeDataResponse.data, path]);

  // Update the `path` URL parameter
  useUpdateEffect(() => {
    if (selectedFile?.filePath !== path) {
      setSearchParams({ path: selectedFile?.filePath || "" });
    }
  }, [selectedFile?.filePath]);

  // Solve a back issue when the archive status change (cf. ANT-2217)
  useUpdateEffect(() => {
    contextValue.reloadTree();
  }, [study.archived]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DebugContext.Provider value={contextValue}>
      <SplitView id="debug" sizes={[20, 80]}>
        <Box sx={{ minWidth: 150, p: 1, overflow: "auto", position: "relative" }}>
          <UsePromiseCond
            keepLastResolvedOnReload
            response={treeDataResponse}
            ifPending={() =>
              Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} height={32} />)
            }
            ifFulfilled={(data) => (
              <Tree
                data={data}
                currentPath={selectedFile?.filePath || null}
                expandedItems={expandedItems}
                setExpandedItems={setExpandedItems}
              />
            )}
          />
        </Box>
        <Box>{selectedFile && <Data {...selectedFile} study={study} />}</Box>
      </SplitView>
    </DebugContext.Provider>
  );
}

export default Debug;
