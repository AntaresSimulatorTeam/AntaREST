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

import SplitView from "@/components/page/SplitView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { buildKey } from "@/utils/reactUtils";
import { Box, Skeleton } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useStudy from "../../../../../-shared/hook/useStudy";
import Data from "./-components/Data";
import DebugContext from "./-components/DebugContext";
import Tree from "./-components/Tree";
import { type FileInfo, getFileType, getTreeData, type TreeData } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/debug/")({
  validateSearch: (search) => ({
    path: (search.path as string) || "",
  }),
  component: Debug,
});

function Debug() {
  const { t } = useTranslation();
  const study = useStudy();
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  // Allow to keep expanded items when the tree is reloaded with `reloadTree`
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const { path } = Route.useSearch();
  const navigate = Route.useNavigate();

  const treeDataResponse = usePromiseWithSnackbarError(() => getTreeData(study.id), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [study.id],
  });

  const { data: treeData, isLoading: isTreeLoading, reload: reloadTree } = treeDataResponse;

  const contextValue = useMemo(
    () => ({
      setPathSearchParam: (path: string) => {
        navigate({ search: { path } });
      },
      isTreeLoading,
      reloadTree,
    }),
    [navigate, isTreeLoading, reloadTree],
  );

  // Update the selected file when the `path` URL parameter or the tree data change
  useUpdateEffect(() => {
    // Avoid updating while the tree is loading
    if (isTreeLoading) {
      return;
    }

    const pathSegments = path?.split("/");
    const filename = pathSegments ? R.last(pathSegments) : null;
    const treeDataForPath = pathSegments ? R.path<TreeData>(pathSegments, treeData) : null;

    // Select the file corresponding to the `path` URL parameter
    if (path && filename && treeDataForPath) {
      setSelectedFile({
        fileType: getFileType(treeDataForPath),
        treeData: treeDataForPath,
        filename,
        filePath: path,
      });

      return;
    }

    const firstChildName = Object.keys(treeData ?? {})[0];
    const firstChildTreeData = R.path<TreeData>([firstChildName], treeData);

    // Select the first child of the tree data
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
  }, [isTreeLoading, treeData, path]);

  // Solve a back issue when the archive status change (cf. ANT-2217)
  useUpdateEffect(() => {
    reloadTree();
  }, [study.archived]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DebugContext.Provider value={contextValue}>
      <SplitView splitId="debug">
        <Box sx={{ p: 1, overflow: "auto", position: "relative" }}>
          <UsePromiseCond
            keepLastResolvedOnReload
            response={treeDataResponse}
            ifPending={() =>
              Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={buildKey("skeleton", index)} height={32} />
              ))
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
