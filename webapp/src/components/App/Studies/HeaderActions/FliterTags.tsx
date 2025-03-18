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

import { Box, Chip, colors } from "@mui/material";
import { displayVersionName } from "@/services/utils";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getGroups, getStudyFilters, getUsers } from "@/redux/selectors";
import { type StudyFilters, updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { useTranslation } from "react-i18next";
import type { GroupDTO, UserDTO } from "@/types/types";
import CustomScrollbar from "@/components/common/CustomScrollbar";

function FilterTags() {
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const filters = useAppSelector(getStudyFilters);

  const users = useAppSelector((state) => {
    return getUsers(state)
      .filter((user) => filters.users.includes(user.id))
      .map((user) => ({ id: user.id, name: user.name }) as UserDTO);
  });

  const groups = useAppSelector((state) => {
    return getGroups(state)
      .filter((group) => filters.groups.includes(group.id))
      .map((group) => ({ id: group.id, name: group.name }) as GroupDTO);
  });

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
        {users.map((user, _) => (
          <Chip
            key={user.id}
            label={user.name}
            onDelete={() => {
              setFilterValue(
                "users",
                filters.users.filter((u) => u !== user.id),
              );
            }}
            sx={{ bgcolor: colors.purple[500] }}
          />
        ))}
        {groups.map((group, _) => (
          <Chip
            key={group.id}
            label={group.name}
            color="success"
            onDelete={() => {
              setFilterValue(
                "groups",
                filters.groups.filter((gp) => gp !== group.id),
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
