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
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudies, getStudyFilters } from "@/redux/selectors";
import ExternalTree from "./ExternalTree";
import ManagedTree from "./ManagedTree";
import TreeSection, { type TreeSectionVariant } from "./TreeSection";
import { studyTreeGridSx } from "./styles";

function StudyTree() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const studies = useAppSelector(getStudies);
  const managedCollapsed = useAppSelector((s) => getStudyFilters(s).managed.collapsed);
  const externalCollapsed = useAppSelector((s) => getStudyFilters(s).external.collapsed);
  const externalStudies = useMemo(() => studies.filter((s) => !s.managed), [studies]);

  const [isCreatingDirectory, setIsCreatingDirectory] = useState(false);

  const gridTemplateRows = `auto ${managedCollapsed ? "0fr" : "1fr"} auto auto ${externalCollapsed ? "0fr" : "1fr"}`;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleManagedRootClick = () => {
    dispatch(
      updateStudyFilters({
        activeTree: "managed",
        managed: { directoryId: null, directoryIds: null },
      }),
    );
  };

  const handleExternalRootClick = () => {
    dispatch(
      updateStudyFilters({
        activeTree: "external",
        external: { path: "" },
      }),
    );
  };

  const handleAddDirectoryClick = () => {
    setIsCreatingDirectory(true);
  };

  const handleDirectoryCreated = () => {
    setIsCreatingDirectory(false);
  };

  const handleToggleCollapse = (section: TreeSectionVariant) => {
    const current = section === "managed" ? managedCollapsed : externalCollapsed;
    dispatch(updateStudyFilters({ [section]: { collapsed: !current } }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={studyTreeGridSx(gridTemplateRows)}>
      <TreeSection
        variant="managed"
        title={t("studies.tree.managed")}
        icon={<AccountTreeIcon />}
        onToggleCollapse={() => handleToggleCollapse("managed")}
        onRootClick={handleManagedRootClick}
        onAddDirectory={handleAddDirectoryClick}
      >
        <ManagedTree
          isCreatingDirectory={isCreatingDirectory}
          onDirectoryCreated={handleDirectoryCreated}
          onRootClick={handleManagedRootClick}
        />
      </TreeSection>

      <Divider />

      <TreeSection
        variant="external"
        title={t("studies.tree.external")}
        icon={<StorageIcon />}
        onToggleCollapse={() => handleToggleCollapse("external")}
        onRootClick={handleExternalRootClick}
      >
        <ExternalTree studies={externalStudies} onRootClick={handleExternalRootClick} />
      </TreeSection>
    </Box>
  );
}

export default StudyTree;
