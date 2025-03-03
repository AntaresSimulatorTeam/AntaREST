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
import { useMemo, useRef, useState } from "react";
import {
  TextField,
  Typography,
  Paper,
  Select,
  MenuItem,
  Box,
  Button,
  InputLabel,
  FormControl,
  ListItem,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  type SelectChangeEvent,
} from "@mui/material";
import { Controller, useFieldArray } from "react-hook-form";
import { v4 as uuidv4 } from "uuid";
import DeleteIcon from "@mui/icons-material/Delete";
import GroupIcon from "@mui/icons-material/Group";
import { RESERVED_GROUP_NAMES, RESERVED_USER_NAMES, ROLE_TYPE_KEYS } from "../../../utils";
import { RoleType, type UserDTO } from "../../../../../../types/types";
import { roleToString, sortByName } from "../../../../../../services/utils";
import usePromise from "../../../../../../hooks/usePromise";
import { getGroups, getUsers } from "../../../../../../services/api/user";
import { getAuthUser } from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import type { UseFormReturnPlus } from "../../../../../common/Form/types";
import { validateString } from "@/utils/validation/string";

function GroupForm(props: UseFormReturnPlus) {
  const {
    control,
    register,
    getValues,
    formState: { errors, defaultValues },
  } = props;

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

  const allowToAddPermission =
    selectedUser &&
    !getValues("permissions").some(({ user }: { user: UserDTO }) => user.id === selectedUser.id);

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
      {/* Name */}
      <TextField
        sx={{ mx: 0 }}
        autoFocus
        label={t("global.name")}
        error={!!errors.name}
        helperText={errors.name?.message?.toString()}
        placeholder={defaultValues?.name}
        InputLabelProps={
          // Allow to show placeholder when field is empty
          defaultValues?.name ? { shrink: true } : {}
        }
        fullWidth
        {...register("name", {
          validate: (v) =>
            validateString(v, {
              existingValues: existingGroups,
              excludedValues: RESERVED_GROUP_NAMES,
              editedValue: defaultValues?.name, // prevent false duplicates on update form
            }),
        })}
      />
      {/* Permissions */}
      <Paper
        sx={{
          p: 2,
          mt: 2,
          backgroundImage: "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
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
                disabled={!allowToAddPermission}
                onClick={() => {
                  append({ user: selectedUser, type: RoleType.READER });
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
                      primary={getValues(`permissions.${index}.user.name`)}
                      title={getValues(`permissions.${index}.user.name`)}
                      sx={{
                        ".MuiTypography-root": {
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                          maxWidth: "325px",
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
