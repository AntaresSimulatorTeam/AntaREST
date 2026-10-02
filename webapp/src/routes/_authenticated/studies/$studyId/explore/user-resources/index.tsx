/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import { getUserResourcesTree } from "@/services/api/studies/userResources";
import { buildKey } from "@/utils/reactUtils";
import { Box, Skeleton } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useStudy from "../../-hooks/useStudy";
import Data from "./-components/Data";
import Tree from "./-components/Tree";
import UserResourcesContext from "./-components/UserResourcesContext";
import {
  getTreeItem,
  getTreeItemType,
  isTreeItemFolder,
  ROOT_FOLDER_NAME,
  ROOT_FOLDER_PATH,
  type TreeItemInfo,
} from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/user-resources/")({
  validateSearch: (search) => ({
    path: (search.path as string) || undefined,
  }),
  component: UserResources,
});

function UserResources() {
  const { t } = useTranslation();
  const study = useStudy();
  const [selectedTreeItem, setSelectedTreeItem] = useState<TreeItemInfo | null>(null);
  // Allow to keep expanded items when the tree is reloaded with `reloadTree`
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const { path } = Route.useSearch();
  const isDatabaseStudy = study.storageMode === "database";

  const treeResponse = usePromiseWithSnackbarError(
    () => getUserResourcesTree({ studyId: study.id }),
    {
      errorMessage: t("studies.error.retrieveData"),
      disabled: !isDatabaseStudy,
      deps: [study.id],
    },
  );

  const { data: tree, isLoading: isTreeLoading, reload: reloadTree } = treeResponse;

  const contextValue = useMemo(
    () => ({
      isTreeLoading,
      reloadTree,
    }),
    [isTreeLoading, reloadTree],
  );

  // Update the selected file when the `path` URL parameter or the tree change
  useUpdateEffect(() => {
    // Avoid updating while the tree is loading
    if (isTreeLoading) {
      return;
    }

    const pathSegments = path?.split("/");
    const treeItem = tree && pathSegments ? getTreeItem(pathSegments, tree) : null;

    // Select the file corresponding to the `path` URL parameter
    if (path && treeItem) {
      setSelectedTreeItem({
        type: getTreeItemType(treeItem),
        name: isTreeItemFolder(treeItem) ? treeItem.name : treeItem,
        path: path,
        data: treeItem,
      });

      return;
    }

    // Display the root folder if no specific path is selected
    if (tree) {
      setSelectedTreeItem({
        type: "folder",
        name: ROOT_FOLDER_NAME,
        path: ROOT_FOLDER_PATH,
        data: { ...tree, name: ROOT_FOLDER_NAME },
      });

      return;
    }

    setSelectedTreeItem(null);
  }, [isTreeLoading, tree, path]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!isDatabaseStudy) {
    throw new Error(`${Route.path} is only available for studies with database storage mode.`);
  }

  return (
    <UserResourcesContext.Provider value={contextValue}>
      <SplitView splitId="user-resources">
        <Box sx={{ p: 1, overflow: "auto", position: "relative" }}>
          <UsePromiseCond
            keepLastResolvedOnReload
            response={treeResponse}
            ifPending={() =>
              Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={buildKey("skeleton", index)} height={32} />
              ))
            }
            ifFulfilled={(data) => (
              <Tree
                data={data}
                currentPath={selectedTreeItem?.path ?? null}
                // Disable the collapse of the root folder by always including it in the expanded items
                expandedItems={[ROOT_FOLDER_PATH, ...expandedItems]}
                setExpandedItems={setExpandedItems}
              />
            )}
          />
        </Box>
        <Box>{selectedTreeItem && <Data {...selectedTreeItem} study={study} />}</Box>
      </SplitView>
    </UserResourcesContext.Provider>
  );
}
