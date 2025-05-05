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
import { getAuthUser, isAuthUserAdmin } from "../../../../../../redux/selectors";
import { getGroups } from "../../../../../../services/api/user";
import { roleToString, sortByName } from "../../../../../../services/utils";
import { RoleType, type GroupDTO } from "../../../../../../types/types";
import { RESERVED_GROUP_NAMES, ROLE_TYPE_KEYS } from "../../../utils";
import type { TokenFormDefaultValues } from "../utils";

interface Props {
  readOnly?: boolean;
}

function TokenForm({ readOnly }: Props) {
  const { control, getValues } = useFormContextPlus<TokenFormDefaultValues>();
  const groupLabelId = useRef(uuidv4()).current;
  const [selectedGroup, setSelectedGroup] = useState<GroupDTO>();
  const { data: groups, isLoading: isGroupsLoading } = usePromise(getGroups);
  const { t } = useTranslation();
  const authUser = useAppSelector(getAuthUser);
  const isUserAdmin = useAppSelector(isAuthUserAdmin);

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
  // Utils
  ////////////////////////////////////////////////////////////////

  const getValidRolesTypesForGroup = (groupName: string) => {
    if (isUserAdmin) {
      return ROLE_TYPE_KEYS;
    }

    const group = authUser?.groups?.find((gp) => gp.name === groupName);
    return group ? ROLE_TYPE_KEYS.filter((key) => RoleType[key] <= group.role) : [];
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset fullFieldWidth>
        <StringFE
          autoFocus={!readOnly}
          label={t("global.name")}
          name="name"
          control={control}
          disabled={readOnly}
          rules={{ validate: validateString() }}
        />
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
            {!readOnly && (
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
            )}
            <List>
              {fields.map((field, index) => (
                <ListItem
                  key={field.id}
                  secondaryAction={
                    <>
                      {!readOnly ? (
                        <Controller
                          control={control}
                          name={`permissions.${index}.type`}
                          render={({ field }) => (
                            <Select variant="standard" {...field}>
                              {getValidRolesTypesForGroup(
                                getValues(`permissions.${index}.group.name`),
                              ).map((key) => (
                                <MenuItem key={key} value={RoleType[key]}>
                                  {roleToString(RoleType[key])}
                                </MenuItem>
                              ))}
                            </Select>
                          )}
                        />
                      ) : (
                        <Typography>
                          {roleToString(getValues(`permissions.${index}.type`))}
                        </Typography>
                      )}
                      {!readOnly && (
                        <IconButton edge="end" onClick={() => remove(index)}>
                          <DeleteIcon />
                        </IconButton>
                      )}
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

export default TokenForm;
