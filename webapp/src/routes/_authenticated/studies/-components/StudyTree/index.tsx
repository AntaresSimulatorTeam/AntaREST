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

import AccountTreeIcon from "@mui/icons-material/AccountTree";
import StorageIcon from "@mui/icons-material/Storage";
import { Box, Divider } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudies } from "@/redux/selectors";
import ExternalTree from "./ExternalTree";
import ManagedTree from "./ManagedTree";
import TreeSection from "./TreeSection";

function StudyTree() {
  const studies = useAppSelector(getStudies);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const [isCreatingFolder, setIsCreatingFolder] = useState(false);

  const managedStudies = studies.filter((s) => s.managed);
  const externalStudies = studies.filter((s) => !s.managed);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleNodeClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
  };

  const handleAddFolderClick = () => {
    setIsCreatingFolder(true);
  };

  const handleFolderCreated = () => {
    setIsCreatingFolder(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box>
      <TreeSection
        variant="managed"
        title={t("studies.tree.managed", { defaultValue: "Managed Studies" })}
        icon={<AccountTreeIcon />}
        onAddFolder={handleAddFolderClick}
      >
        <ManagedTree
          studies={managedStudies}
          onNodeClick={handleNodeClick}
          isCreatingFolder={isCreatingFolder}
          onFolderCreated={handleFolderCreated}
        />
      </TreeSection>

      <Divider />

      <TreeSection
        variant="external"
        title={t("studies.tree.external", { defaultValue: "External Storage" })}
        //subtitle={t("studies.tree.readOnly", { defaultValue: "(read-only)" })}
        icon={<StorageIcon />}
      >
        <ExternalTree studies={externalStudies} onNodeClick={handleNodeClick} />
      </TreeSection>
    </Box>
  );
}

export default StudyTree;
