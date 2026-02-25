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
import { getStudies } from "@/redux/selectors";
import ExternalTree from "./ExternalTree";
import ManagedTree from "./ManagedTree";
import TreeSection from "./TreeSection";

function StudyTree() {
  const studies = useAppSelector(getStudies);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const [isCreatingDirectory, setIsCreatingDirectory] = useState(false);

  //const managedStudies = useMemo(() => studies.filter((s) => s.managed), [studies]);
  const externalStudies = useMemo(() => studies.filter((s) => !s.managed), [studies]);

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
        external: { path: "", strictPath: false },
      }),
    );
  };

  const handleAddDirectoryClick = () => {
    setIsCreatingDirectory(true);
  };

  const handleDirectoryCreated = () => {
    setIsCreatingDirectory(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box>
      <TreeSection
        variant="managed"
        title={t("studies.tree.managed")}
        icon={<AccountTreeIcon />}
        onRootClick={handleManagedRootClick}
        onAddDirectory={handleAddDirectoryClick}
      >
        <ManagedTree
          // studies={managedStudies}
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
        onRootClick={handleExternalRootClick}
      >
        <ExternalTree studies={externalStudies} onRootClick={handleExternalRootClick} />
      </TreeSection>
    </Box>
  );
}

export default StudyTree;
