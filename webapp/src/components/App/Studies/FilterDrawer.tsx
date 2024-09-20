/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Divider from "@mui/material/Divider";
import { Button, Drawer, List, ListItem, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { STUDIES_FILTER_WIDTH } from "../../../theme";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import {
  getGroups,
  getStudyFilters,
  getStudyVersions,
  getUsers,
} from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { StudyFilters, updateStudyFilters } from "../../../redux/ducks/studies";
import CheckboxesTagsFE from "../../common/fieldEditors/CheckboxesTagsFE";
import { displayVersionName } from "../../../services/utils";
import CheckBoxFE from "../../common/fieldEditors/CheckBoxFE";

interface Props {
  open: boolean;
  onClose: () => void;
}

function FilterDrawer(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const filters = useAppSelector(getStudyFilters);
  const versions = useAppSelector(getStudyVersions);
  const users = useAppSelector(getUsers);
  const groups = useAppSelector(getGroups);
  const dispatch = useAppDispatch();
  const filterNewValuesRef = useRef<Partial<StudyFilters>>({});

  useEffect(() => {
    filterNewValuesRef.current = {};
  }, [open]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFilter = () => {
    dispatch(updateStudyFilters(filterNewValuesRef.current));
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
      sx={{
        width: STUDIES_FILTER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: STUDIES_FILTER_WIDTH,
          boxSizing: "border-box",
          overflow: "hidden",
        },
      }}
    >
      <Toolbar sx={{ py: 3 }}>
        <Box
          display="flex"
          width="100%"
          height="100%"
          justifyContent="flex-start"
          alignItems="flex-start"
          py={2}
          flexDirection="column"
          flexWrap="nowrap"
          boxSizing="border-box"
          color="white"
        >
          <Typography sx={{ color: "grey.500", fontSize: "0.9em", mb: 2 }}>
            {t("global.filter").toUpperCase()}
          </Typography>
          <CheckBoxFE
            defaultValue={filters.managed}
            onChange={(_, checked) => {
              filterNewValuesRef.current.managed = checked;
            }}
            label={t("studies.managedStudiesFilter")}
          />
          <CheckBoxFE
            defaultValue={filters.archived}
            onChange={(_, checked) => {
              filterNewValuesRef.current.archived = checked;
            }}
            label={t("studies.archivedStudiesFilter")}
          />
          <CheckBoxFE
            defaultValue={filters.variant}
            onChange={(_, checked) => {
              filterNewValuesRef.current.variant = checked;
            }}
            label={t("studies.variant")}
          />
        </Box>
      </Toolbar>
      <Divider style={{ height: "1px", backgroundColor: "grey.800" }} />
      <List>
        <ListItem>
          <CheckboxesTagsFE
            label={t("global.versions")}
            options={versions}
            getOptionLabel={displayVersionName}
            defaultValue={filters.versions}
            onChange={(event) => {
              filterNewValuesRef.current.versions = event.target.value;
            }}
            fullWidth
          />
        </ListItem>
        <ListItem>
          <CheckboxesTagsFE
            label={t("global.users")}
            options={users}
            getOptionLabel={(option) => option.name}
            defaultValue={users.filter((user) =>
              filters.users.includes(user.id),
            )}
            onChange={(event) => {
              filterNewValuesRef.current.users = event.target.value.map(
                (val) => val.id,
              );
            }}
            fullWidth
          />
        </ListItem>
        <ListItem>
          <CheckboxesTagsFE
            label={t("global.groups")}
            options={groups}
            getOptionLabel={(option) => option.name}
            defaultValue={groups.filter((group) =>
              filters.groups.includes(group.id),
            )}
            onChange={(event) => {
              filterNewValuesRef.current.groups = event.target.value.map(
                (val) => val.id,
              );
            }}
            fullWidth
          />
        </ListItem>
        <ListItem>
          <CheckboxesTagsFE
            label={t("global.tags")}
            options={[]}
            defaultValue={filters.tags}
            onChange={(event) => {
              filterNewValuesRef.current.tags = event.target.value;
            }}
            freeSolo
            fullWidth
          />
        </ListItem>
      </List>
      <Box
        display="flex"
        width="100%"
        flexGrow={1}
        justifyContent="flex-end"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          width="100%"
          height="auto"
          justifyContent="flex-end"
          alignItems="center"
          flexDirection="row"
          flexWrap="nowrap"
          boxSizing="border-box"
          p={1}
        >
          <Button variant="outlined" onClick={handleReset}>
            {t("global.reset")}
          </Button>
          <Button sx={{ mx: 2 }} variant="contained" onClick={handleFilter}>
            {t("global.filter")}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}

export default FilterDrawer;
