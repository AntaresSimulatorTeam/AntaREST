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

import PasswordFE from "@/components/common/fieldEditors/PasswordFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import { useFormContextPlus } from "@/components/common/Form";
import { validatePassword, validateString } from "@/utils/validation/string";
import DeleteIcon from "@mui/icons-material/Delete";
import GroupIcon from "@mui/icons-material/Group";
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Tooltip,
  Typography,
  type SelectChangeEvent,
} from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { Controller, useFieldArray, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { v4 as uuidv4 } from "uuid";
import type { UserFormDialogProps } from ".";
import usePromise from "../../../../../../hooks/usePromise";
import { getGroups, getUsers } from "../../../../../../services/api/user";
import { roleToString, sortByName } from "../../../../../../services/utils";
import { RoleType, type GroupDTO } from "../../../../../../types/types";
import { RESERVED_GROUP_NAMES, RESERVED_USER_NAMES, ROLE_TYPE_KEYS } from "../../../utils";
import type { UserFormDefaultValues } from "../utils";

interface Props {
  onlyPermissions?: UserFormDialogProps["onlyPermissions"];
}

function UserForm({ onlyPermissions }: Props) {
  const {
    control,
    getValues,
    formState: { defaultValues },
  } = useFormContextPlus<UserFormDefaultValues>();

  const { t } = useTranslation();
  const groupLabelId = useRef(uuidv4()).current;
  const [selectedGroup, setSelectedGroup] = useState<GroupDTO>();
  const { data: groups, isLoading: isGroupsLoading } = usePromise(getGroups);
  const { data: users } = usePromise(getUsers);
  const existingUsers = useMemo(() => users?.map(({ name }) => name), [users]);

  const { fields, append, remove } = useFieldArray({
    control,
    name: "permissions",
  });

  const permissions = useWatch({ control, name: "permissions" });

  const canAddPermission =
    selectedGroup && !permissions.some(({ group }) => group.id === selectedGroup.id);

  const filteredAndSortedGroups = useMemo(() => {
    if (!groups) {
      return [];
    }
    return sortByName(groups.filter((group) => !RESERVED_GROUP_NAMES.includes(group.name)));
  }, [groups]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleGroupChange = (event: SelectChangeEvent<string>) => {
    const groupId = event.target.value;
    const group = groups?.find((gp) => gp.id === groupId);
    setSelectedGroup(group);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset fullFieldWidth>
        <StringFE
          autoFocus
          label={t("global.username")}
          name="username"
          control={control}
          disabled={onlyPermissions}
          rules={{
            validate: validateString({
              existingValues: existingUsers,
              excludedValues: RESERVED_USER_NAMES,
              editedValue: defaultValues?.username,
            }),
          }}
        />
        {!onlyPermissions && (
          <>
            <PasswordFE
              label={t("global.password")}
              name="password"
              control={control}
              rules={{
                validate: validatePassword,
              }}
            />
            <PasswordFE
              label={t("settings.user.form.confirmPassword")}
              name="confirmPassword"
              control={control}
              rules={{
                validate: (v) =>
                  v === getValues("password") || t("settings.user.form.error.passwordMismatch"),
              }}
            />
          </>
        )}
      </Fieldset>
      {/* Permissions */}
      <Paper sx={{ p: 2 }}>
        <Typography>{t("global.permissions")}</Typography>
        {isGroupsLoading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignContent: "center",
              mt: 2,
            }}
          >
            <CircularProgress color="inherit" />
          </Box>
        )}
        {filteredAndSortedGroups.length > 0 && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
              <FormControl sx={{ mr: 2, flex: 1 }}>
                <InputLabel id={groupLabelId}>{t("global.group")}</InputLabel>
                <Select
                  labelId={groupLabelId}
                  label={t("global.group")}
                  defaultValue=""
                  onChange={handleGroupChange}
                >
                  {filteredAndSortedGroups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                disabled={!canAddPermission}
                onClick={() => {
                  if (canAddPermission) {
                    append({ group: selectedGroup, type: RoleType.READER });
                  }
                }}
              >
                {t("button.add")}
              </Button>
            </Box>
            <List>
              {fields.map((field, index) => (
                <ListItem
                  key={field.id}
                  secondaryAction={
                    <>
                      <Controller
                        control={control}
                        name={`permissions.${index}.type`}
                        render={({ field }) => (
                          <Select variant="standard" {...field}>
                            {ROLE_TYPE_KEYS.map((key) => (
                              <MenuItem key={key} value={RoleType[key]}>
                                {roleToString(RoleType[key])}
                              </MenuItem>
                            ))}
                          </Select>
                        )}
                      />
                      <IconButton edge="end" onClick={() => remove(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </>
                  }
                  disablePadding
                  dense
                >
                  <ListItemButton sx={{ cursor: "default" }} disableRipple disableGutters>
                    <ListItemIcon sx={{ minWidth: 0, p: "0 15px 0 5px" }}>
                      <GroupIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Tooltip title={getValues(`permissions.${index}.group.name`)}>
                          <span>{getValues(`permissions.${index}.group.name`)}</span>
                        </Tooltip>
                      }
                      sx={{
                        ".MuiTypography-root": {
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                          maxWidth: 185,
                          whiteSpace: "nowrap",
                        },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </>
        )}
      </Paper>
    </>
  );
}

export default UserForm;
