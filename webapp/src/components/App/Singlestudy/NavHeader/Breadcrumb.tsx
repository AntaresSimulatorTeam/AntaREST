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
import { buildBreadcrumbPath } from "./utils";

interface BreadcrumbProps {
  studyId: string;
  studyName: string;
  workspace: string;
  folder?: string;
}

function Breadcrumb({ studyId, studyName, workspace, folder }: BreadcrumbProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const pathHierarchy = buildBreadcrumbPath({
    folderPath: folder,
    workspaceName: workspace,
    studyName,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleBreadcrumbClick = (folderPath: string, isLastSegment: boolean) => {
    if (isLastSegment) {
      // Navigate to the specific study's detail page when clicking the study name
      // This allows users to go back to the study overview from any sub-page
      navigate(`/studies/${studyId}`);
    } else {
      // Navigate to studies list with folder filter when clicking folder segments
      // This allows users to browse other studies in the same folder hierarchy
      dispatch(updateStudyFilters({ folder: `/${folderPath}` }));
      navigate("/studies");
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center" }}>
      <Breadcrumbs maxItems={5} sx={{ fontSize: 15 }}>
        {pathHierarchy.map((folderName, index) => {
          const path = pathHierarchy.slice(0, index + 1).join("/");
          const isFirstSegment = index === 0;
          const isLastSegment = index === pathHierarchy.length - 1;

          return (
            <BreadcrumbLink
              key={path}
              folderName={folderName}
              isFirstSegment={isFirstSegment}
              onClick={() => handleBreadcrumbClick(path, isLastSegment)}
            />
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default Breadcrumb;
