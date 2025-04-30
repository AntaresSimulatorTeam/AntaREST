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

import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import { useFormContextPlus } from "@/components/common/Form";
import { validateString } from "@/utils/validation/string";
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
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAuthUser } from "../../../../../../redux/selectors";
import { getGroups, getUsers } from "../../../../../../services/api/user";
import { roleToString, sortByName } from "../../../../../../services/utils";
import { RoleType, type UserDTO } from "../../../../../../types/types";
import { RESERVED_GROUP_NAMES, RESERVED_USER_NAMES, ROLE_TYPE_KEYS } from "../../../utils";
import type { GroupFormDefaultValues } from "../utils";

function GroupForm() {
  const {
    control,
    getValues,
    formState: { defaultValues },
  } = useFormContextPlus<GroupFormDefaultValues>();

  const { t } = useTranslation();
  const authUser = useAppSelector(getAuthUser);
  const userLabelId = useRef(uuidv4()).current;
  const [selectedUser, setSelectedUser] = useState<UserDTO>();
  const { data: users, isLoading: isUsersLoading } = usePromise(getUsers);
  const { data: groups } = usePromise(getGroups);

  const existingGroups = useMemo(() => groups?.map((group) => group.name), [groups]);

  const { fields, append, remove } = useFieldArray({
    control,
    name: "permissions",
  });

  const permissions = useWatch({ control, name: "permissions" });

  const canAddPermission =
    selectedUser && !permissions.some(({ user }) => user.id === selectedUser.id);

  const filteredAndSortedUsers = useMemo(() => {
    if (!users) {
      return [];
    }

    return sortByName(
      users.filter((user) => !RESERVED_USER_NAMES.includes(user.name) && user.id !== authUser?.id),
    );
  }, [users, authUser]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUserChange = (event: SelectChangeEvent<string>) => {
    const userId = Number(event.target.value);
    const user = users?.find((u) => u.id === userId);
    setSelectedUser(user);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset fullFieldWidth>
        <StringFE
          autoFocus
          label={t("global.name")}
          name="name"
          control={control}
          rules={{
            validate: validateString({
              existingValues: existingGroups,
              excludedValues: RESERVED_GROUP_NAMES,
              editedValue: defaultValues?.name,
            }),
          }}
        />
      </Fieldset>
      {/* Permissions */}
      <Paper sx={{ p: 2 }}>
        <Typography>{t("global.permissions")}</Typography>
        {isUsersLoading && (
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
        {filteredAndSortedUsers.length > 0 && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
              <FormControl sx={{ mr: 2, flex: 1 }}>
                <InputLabel id={userLabelId}>{t("global.user")}</InputLabel>
                <Select
                  labelId={userLabelId}
                  label={t("global.user")}
                  defaultValue=""
                  onChange={handleUserChange}
                >
                  {filteredAndSortedUsers.map((user) => (
                    <MenuItem key={user.id} value={user.id}>
                      {user.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                disabled={!canAddPermission}
                onClick={() => {
                  if (canAddPermission) {
                    append({ user: selectedUser, type: RoleType.READER });
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
                        <Tooltip title={getValues(`permissions.${index}.user.name`)}>
                          <span>{getValues(`permissions.${index}.user.name`)}</span>
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

export default GroupForm;
