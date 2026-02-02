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

import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import type { StudyMetadata } from "@/types/types";
import HomeIcon from "@mui/icons-material/Home";
import { Box, Breadcrumbs } from "@mui/material";
import BreadcrumbLink from "./BreadcrumbLink";
import { buildBreadcrumbPath } from "./utils";

interface BreadcrumbProps {
  study: StudyMetadata;
}

function Breadcrumb({ study }: BreadcrumbProps) {
  const dispatch = useAppDispatch();

  const breadcrumbPath = buildBreadcrumbPath({
    folderPath: study.folder,
    workspaceName: study.workspace,
    studyName: study.name,
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center" }}>
      <Breadcrumbs maxItems={5} sx={{ fontSize: 15 }}>
        {breadcrumbPath.map((folderName, index) => {
          const folderPath = `/${breadcrumbPath.slice(0, index + 1).join("/")}`;
          const isFirstSegment = index === 0;
          const isLastSegment = index === breadcrumbPath.length - 1;

          return (
            <BreadcrumbLink
              key={folderPath}
              label={folderName}
              icon={isFirstSegment ? <HomeIcon fontSize="inherit" sx={{ mr: 1 }} /> : null}
              // Study names (last segment) are never truncated to prevent users from accidentally
              // working with the wrong study due to similar truncated names.
              truncate={!isLastSegment}
              linkOptions={
                isLastSegment
                  ? { to: "/studies/$studyId", params: { studyId: study.id } }
                  : { to: "/studies" }
              }
              onClick={() => {
                if (!isLastSegment) {
                  // This allows users to browse other studies in the same folder hierarchy
                  dispatch(updateStudyFilters({ folder: folderPath }));
                }
              }}
            />
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default Breadcrumb;
