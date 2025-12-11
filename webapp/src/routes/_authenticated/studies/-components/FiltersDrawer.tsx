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

import CheckboxesTagsFE from "@/components/fieldEditors/CheckboxesTagsFE";
import SelectFE, { type Options } from "@/components/fieldEditors/SelectFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { updateStudyFilters, type StudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import {
  getGroupIds,
  getGroupsById,
  getStudyFilters,
  getStudyVersions,
  getUserIds,
  getUsersById,
} from "@/redux/selectors";
import { compactSemanticVersion } from "@/utils/versionUtils";
import FilterAltIcon from "@mui/icons-material/FilterAlt";
import { Box, Button, Drawer, Toolbar, Typography } from "@mui/material";
import { useId } from "react";
import { useTranslation } from "react-i18next";

const STUDY_TYPE_OPTIONS: Options<StudyFilters["type"]> = [
  { label: (t) => t("global.all"), value: "all" },
  { label: (t) => t("studies.references"), value: "references" },
  { label: (t) => t("studies.variants"), value: "variants" },
];

const MANAGEMENT_OPTIONS: Options<StudyFilters["management"]> = [
  { label: (t) => t("global.all"), value: "all" },
  { label: (t) => t("studies.managed"), value: "managed" },
  { label: (t) => t("studies.unmanaged"), value: "unmanaged" },
];

const ARCHIVE_OPTIONS: Options<StudyFilters["archive"]> = [
  { label: (t) => t("global.all"), value: "all" },
  { label: (t) => t("studies.archived"), value: "archived" },
  { label: (t) => t("studies.unarchived"), value: "unarchived" },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

function FiltersDrawer(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const filters = useAppSelector(getStudyFilters);
  const versions = useAppSelector(getStudyVersions);
  const usersById = useAppSelector(getUsersById);
  const userIds = useAppSelector(getUserIds);
  const groupsById = useAppSelector(getGroupsById);
  const groupIds = useAppSelector(getGroupIds);
  const dispatch = useAppDispatch();
  const formId = useId();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<StudyFilters>) => {
    dispatch(updateStudyFilters(values));

    onClose();
  };

  const handleReset = () => {
    dispatch(
      updateStudyFilters({
        management: "all",
        archive: "all",
        type: "references",
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
        id={formId}
        onSubmit={handleSubmit}
        sx={{ p: 2 }}
        hideSubmitButton
      >
        {({ control }) => (
          <>
            <Fieldset fullFieldWidth>
              <SelectFE
                label={t("study.type")}
                name="type"
                control={control}
                options={STUDY_TYPE_OPTIONS}
              />
              <SelectFE
                label={t("studies.filters.management")}
                name="management"
                control={control}
                options={MANAGEMENT_OPTIONS}
              />
              <SelectFE
                label={t("studies.filters.archive")}
                name="archive"
                control={control}
                options={ARCHIVE_OPTIONS}
              />
              <CheckboxesTagsFE
                name="versions"
                control={control}
                label={t("global.versions")}
                options={versions}
                getOptionLabel={compactSemanticVersion}
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

export default FiltersDrawer;
