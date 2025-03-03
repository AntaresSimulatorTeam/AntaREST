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

import { useTranslation } from "react-i18next";
import { Box, Button, Drawer, Toolbar, Typography } from "@mui/material";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import {
  getGroupIds,
  getGroupsById,
  getStudyFilters,
  getStudyVersions,
  getUserIds,
  getUsersById,
} from "@/redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudyFilters, type StudyFilters } from "@/redux/ducks/studies";
import CheckboxesTagsFE from "../../common/fieldEditors/CheckboxesTagsFE";
import { displayVersionName } from "@/services/utils";
import CheckBoxFE from "../../common/fieldEditors/CheckBoxFE";
import Form from "@/components/common/Form";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import FilterAltIcon from "@mui/icons-material/FilterAlt";

interface Props {
  open: boolean;
  onClose: () => void;
}

function FilterDrawer(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const filters = useAppSelector(getStudyFilters);
  const versions = useAppSelector(getStudyVersions);
  const usersById = useAppSelector(getUsersById);
  const userIds = useAppSelector(getUserIds);
  const groupsById = useAppSelector(getGroupsById);
  const groupIds = useAppSelector(getGroupIds);
  const dispatch = useAppDispatch();
  const formId = "studies-filter-drawer";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values, dirtyValues }: SubmitHandlerPlus<StudyFilters>) => {
    const { users, groups, versions, tags, ...rest } = dirtyValues;

    const newFilters: Partial<StudyFilters> = rest;

    if (users) {
      newFilters.users = values.users;
    }

    if (groups) {
      newFilters.groups = values.groups;
    }

    if (versions) {
      newFilters.versions = values.versions;
    }

    if (tags) {
      newFilters.tags = values.tags;
    }

    dispatch(updateStudyFilters(newFilters));

    onClose();
  };

  const handleReset = () => {
    dispatch(
      updateStudyFilters({
        managed: false,
        archived: false,
        variant: false,
        versions: [],
        users: [],
        groups: [],
        tags: [],
      }),
    );

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      variant="temporary"
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: 300 } }}
    >
      <Toolbar>
        <FilterAltIcon sx={{ mr: 1 }} />
        <Typography variant="h6">{t("global.filters")}</Typography>
      </Toolbar>
      <Form
        config={{ defaultValues: filters }}
        id="studies-filter-drawer"
        onSubmit={handleSubmit}
        sx={{ p: 2 }}
        hideSubmitButton
      >
        {({ control }) => (
          <>
            <Fieldset fullFieldWidth>
              <CheckBoxFE
                name="managed"
                control={control}
                label={t("studies.managedStudiesFilter")}
              />
              <CheckBoxFE
                name="archived"
                control={control}
                label={t("studies.archivedStudiesFilter")}
              />
              <CheckBoxFE name="variant" control={control} label={t("studies.variant")} />
              <CheckboxesTagsFE
                name="versions"
                control={control}
                label={t("global.versions")}
                options={versions}
                getOptionLabel={displayVersionName}
              />
              <CheckboxesTagsFE
                name="users"
                control={control}
                label={t("global.users")}
                options={userIds}
                getOptionLabel={(option) => usersById[option]?.name ?? option.toString()}
              />
              <CheckboxesTagsFE
                name="groups"
                control={control}
                label={t("global.groups")}
                options={groupIds}
                getOptionLabel={(option) => groupsById[option]?.name ?? option.toString()}
              />
              <CheckboxesTagsFE
                name="tags"
                control={control}
                label={t("global.tags")}
                options={[]}
                defaultValue={filters.tags}
                freeSolo
              />
            </Fieldset>
          </>
        )}
      </Form>
      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, p: 1 }}>
        <Button variant="outlined" onClick={handleReset}>
          {t("global.reset")}
        </Button>
        <Button variant="contained" type="submit" form={formId}>
          {t("global.filterAction")}
        </Button>
      </Box>
    </Drawer>
  );
}

export default FilterDrawer;
