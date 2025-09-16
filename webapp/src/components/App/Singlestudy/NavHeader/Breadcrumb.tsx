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

import { Box, Breadcrumbs } from "@mui/material";
import { useNavigate } from "react-router";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import BreadcrumbLink from "./BreadcrumbLink";
import { buildBreadcrumbPath, shouldShowBreadcrumb } from "./utils";

interface BreadcrumbProps {
  studyId: string;
  workspace: string;
  folder?: string;
}

function Breadcrumb({ studyId, workspace, folder }: BreadcrumbProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleBreadcrumbClick = (folderPath: string) => {
    dispatch(updateStudyFilters({ folder: `/${folderPath}` }));
    navigate("/studies");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!folder) {
    return null;
  }

  const pathHierarchy = buildBreadcrumbPath(folder, workspace, studyId);

  if (!shouldShowBreadcrumb(pathHierarchy)) {
    return null;
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center" }}>
      <Breadcrumbs maxItems={5} sx={{ fontSize: 13 }}>
        {pathHierarchy.map((folderName, index) => {
          const path = pathHierarchy.slice(0, index + 1).join("/");
          const isFirstSegment = index === 0;

          return (
            <BreadcrumbLink
              key={path}
              folderName={folderName}
              isFirstSegment={isFirstSegment}
              onClick={() => handleBreadcrumbClick(path)}
            />
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default Breadcrumb;
