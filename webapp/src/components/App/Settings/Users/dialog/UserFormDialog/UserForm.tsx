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
  SelectChangeEvent,
} from "@mui/material";
import { Controller, useFieldArray } from "react-hook-form";
import { v4 as uuidv4 } from "uuid";
import DeleteIcon from "@mui/icons-material/Delete";
import GroupIcon from "@mui/icons-material/Group";
import {
  RESERVED_GROUP_NAMES,
  RESERVED_USER_NAMES,
  ROLE_TYPE_KEYS,
} from "../../../utils";
import { GroupDTO, RoleType } from "../../../../../../common/types";
import { roleToString, sortByName } from "../../../../../../services/utils";
import usePromise from "../../../../../../hooks/usePromise";
import { getGroups } from "../../../../../../services/api/user";
import { UserFormDialogProps } from ".";
import { UseFormReturnPlus } from "../../../../../common/Form";

interface Props extends UseFormReturnPlus {
  onlyPermissions?: UserFormDialogProps["onlyPermissions"];
}

const PASSWORD_MIN_LENGTH = 8;

function UserForm(props: Props) {
  const {
    control,
    register,
    getValues,
    formState: { errors },
    onlyPermissions,
  } = props;

  const groupLabelId = useRef(uuidv4()).current;
  const { fields, append, remove } = useFieldArray({
    control,
    name: "permissions",
  });
  const [selectedGroup, setSelectedGroup] = useState<GroupDTO>();
  const { data: groups, isLoading: isGroupsLoading } = usePromise(getGroups);
  const { t } = useTranslation();
  const commonTextFieldProps = {
    required: true,
    sx: { mx: 0 },
    fullWidth: true,
  };
  const allowToAddPermission =
    selectedGroup &&
    !getValues("permissions").some(
      ({ group }: { group: GroupDTO }) => group.id === selectedGroup.id
    );

  const filteredAndSortedGroups = useMemo(() => {
    if (!groups) {
      return [];
    }
    return sortByName(
      groups.filter((group) => !RESERVED_GROUP_NAMES.includes(group.name))
    );
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
      {/* Login credentials */}
      {!onlyPermissions && (
        <>
          <TextField
            autoFocus
            label={t("global.username")}
            error={!!errors?.username}
            helperText={errors?.username?.message}
            {...commonTextFieldProps}
            {...register("username", {
              required: t("form.field.required") as string,
              validate: (value) => {
                if (RESERVED_USER_NAMES.includes(value)) {
                  return t("form.field.notAllowedValue") as string;
                }
              },
            })}
          />
          <TextField
            label={t("global.password")}
            type="password"
            error={!!errors?.password}
            helperText={errors?.password?.message}
            {...commonTextFieldProps}
            {...register("password", {
              required: t("form.field.required") as string,
              minLength: {
                value: PASSWORD_MIN_LENGTH,
                message: t("form.field.minLength", [PASSWORD_MIN_LENGTH]),
              },
            })}
          />
        </>
      )}
      {/* Permissions */}
      <Paper
        sx={{
          p: 2,
          mt: 2,
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
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
              <FormControl sx={{ mr: 2, flex: 1 }} size="small">
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
                size="small"
                disabled={!allowToAddPermission}
                onClick={() => {
                  append({ group: selectedGroup, type: RoleType.READER });
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
                  <ListItemButton
                    sx={{ cursor: "default" }}
                    disableRipple
                    disableGutters
                  >
                    <ListItemIcon sx={{ minWidth: 0, p: "0 15px 0 5px" }}>
                      <GroupIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={getValues(`permissions.${index}.group.name`)}
                      title={getValues(`permissions.${index}.group.name`)}
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

UserForm.defaultProps = {
  onlyPermissions: false,
};

export default UserForm;
