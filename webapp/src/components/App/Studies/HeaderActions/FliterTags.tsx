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

import CustomScrollbar from "@/components/common/CustomScrollbar";
import { type StudyFilters, updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getGroups, getStudyFilters, getUsers } from "@/redux/selectors";
import { displayVersionName } from "@/services/utils";
import { Box, Chip, colors } from "@mui/material";
import { useTranslation } from "react-i18next";

function FilterTags() {
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const filters = useAppSelector(getStudyFilters);
  const users = useAppSelector(getUsers);
  const groups = useAppSelector(getGroups);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setFilterValue = <T extends keyof StudyFilters>(string: T, newValue: StudyFilters[T]) => {
    dispatch(updateStudyFilters({ [string]: newValue }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <CustomScrollbar>
      <Box
        sx={{
          display: "flex",
          gap: 0.5,
        }}
      >
        {filters.managed && (
          <Chip
            label={t("studies.managedStudiesFilter")}
            color="secondary"
            onDelete={() => setFilterValue("managed", false)}
          />
        )}
        {filters.archived && (
          <Chip
            label={t("studies.archivedStudiesFilter")}
            color="secondary"
            onDelete={() => setFilterValue("archived", false)}
          />
        )}
        {filters.variant && (
          <Chip
            label={t("studies.variant").toLowerCase()}
            color="secondary"
            onDelete={() => setFilterValue("variant", false)}
          />
        )}
        {filters.versions.map((version) => (
          <Chip
            key={version}
            label={displayVersionName(version)}
            color="primary"
            onDelete={() => {
              setFilterValue(
                "versions",
                filters.versions.filter((ver) => ver !== version),
              );
            }}
          />
        ))}
        {filters.users.map((userId) => (
          <Chip
            key={userId}
            label={users.find(({ id }) => id === userId)?.name}
            onDelete={() => {
              setFilterValue(
                "users",
                filters.users.filter((id) => id !== userId),
              );
            }}
            sx={{ bgcolor: colors.purple[500] }}
          />
        ))}
        {filters.groups.map((groupId) => (
          <Chip
            key={groupId}
            label={groups.find(({ id }) => id === groupId)?.name}
            color="success"
            onDelete={() => {
              setFilterValue(
                "groups",
                filters.groups.filter((id) => id !== groupId),
              );
            }}
          />
        ))}
        {filters.tags.map((tag, _, tags) => (
          <Chip
            key={tag}
            label={tag}
            onDelete={() => {
              setFilterValue(
                "tags",
                tags.filter((t) => t !== tag),
              );
            }}
            sx={{ color: "black", bgcolor: colors.indigo[300] }}
          />
        ))}
      </Box>
    </CustomScrollbar>
  );
}

export default FilterTags;
