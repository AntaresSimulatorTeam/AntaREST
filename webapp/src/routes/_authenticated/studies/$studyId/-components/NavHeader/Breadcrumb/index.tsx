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

import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import { buildKey } from "@/utils/reactUtils";
import HomeIcon from "@mui/icons-material/Home";
import { Breadcrumbs } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import useStudy from "../../../-hooks/useStudy";
import BreadcrumbLink from "./BreadcrumbLink";
import { buildExternalBreadcrumbs, buildManagedBreadcrumbs } from "./utils";

function Breadcrumb() {
  const study = useStudy();
  const dispatch = useAppDispatch();
  const filters = useAppSelector(getStudyFilters);
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  // Build breadcrumbs based on study type (managed vs external)
  const breadcrumbItems = study.managed
    ? buildManagedBreadcrumbs({
        directoryId: study.directoryId ?? null,
        studyName: study.name,
        directories,
      })
    : buildExternalBreadcrumbs({
        folderPath: study.folder,
        workspaceName: study.workspace,
        studyName: study.name,
      });

  const handleBreadcrumbClick = (index: number) => {
    const item = breadcrumbItems[index];
    const isLastSegment = index === breadcrumbItems.length - 1;

    // Last segment (study name) doesn't trigger filter updates - it just navigates
    if (isLastSegment) {
      return;
    }

    if (study.managed) {
      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: {
            directoryId: item.id,
            directoryIds: item.id ? getDescendantIds(item.id, directories) : null,
          },
        }),
      );
    } else {
      dispatch(
        updateStudyFilters({
          activeTree: "external",
          external: {
            path: item.path || "/",
            strictPath: filters.external.strictPath,
          },
        }),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Breadcrumbs maxItems={5} sx={{ fontSize: 15, flex: 1 }}>
      {breadcrumbItems.map((item, index) => {
        const isFirstSegment = index === 0;
        const isLastSegment = index === breadcrumbItems.length - 1;

        return (
          <BreadcrumbLink
            key={buildKey(item.label, index)}
            label={item.label}
            icon={isFirstSegment ? <HomeIcon fontSize="inherit" sx={{ mr: 1 }} /> : null}
            // Study names (last segment) are never truncated to prevent users from accidentally
            // working with the wrong study due to similar truncated names.
            truncate={!isLastSegment}
            linkOptions={
              isLastSegment
                ? { to: "/studies/$studyId", params: { studyId: study.id } }
                : { to: "/studies" }
            }
            onClick={() => handleBreadcrumbClick(index)}
          />
        );
      })}
    </Breadcrumbs>
  );
}

export default Breadcrumb;
