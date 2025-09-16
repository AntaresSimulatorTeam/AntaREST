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

import HomeIcon from "@mui/icons-material/Home";
import { Box, Breadcrumbs, Link } from "@mui/material";
import { useNavigate } from "react-router";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { buildBreadcrumbPath, shouldShowBreadcrumb } from "./utils";

interface Props {
  studyId: string;
  workspace: string;
  folder?: string;
}

function Breadcrumb({ studyId, workspace, folder }: Props) {
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
      <Breadcrumbs maxItems={5} sx={{ fontSize: "0.875rem" }}>
        {pathHierarchy.map((folderName, index) => {
          const path = pathHierarchy.slice(0, index + 1).join("/");
          const isFirstSegment = index === 0;

          return (
            <Link
              key={path}
              underline={isFirstSegment ? "none" : "hover"}
              color="inherit"
              onClick={() => handleBreadcrumbClick(path)}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                fontSize: "0.875rem",
              }}
            >
              {isFirstSegment ? (
                <>
                  <HomeIcon fontSize="inherit" sx={{ marginRight: 0.5 }} />
                  {folderName}
                </>
              ) : (
                folderName
              )}
            </Link>
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default Breadcrumb;
