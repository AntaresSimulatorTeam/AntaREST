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
import { RoleType, UserDTO } from "../../../../../common/types";
import { roleToString, sortByName } from "../../../../../services/utils";
import usePromise from "../../../../../hooks/usePromise";
import { getUsers } from "../../../../../services/api/user";
import { getAuthUser } from "../../../../../redux/selectors";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { FormObj } from "../../../../common/Form";

function GroupForm(props: FormObj) {
  const {
    control,
    register,
    getValues,
    formState: { errors },
    defaultValues,
  } = props;

  const userLabelId = useRef(uuidv4()).current;
  const { fields, append, remove } = useFieldArray({
    control,
    name: "permissions",
  });
  const [selectedUser, setSelectedUser] = useState<UserDTO>();
  const { data: users, isLoading: isUsersLoading } = usePromise(getUsers);
  const { t } = useTranslation();
  const authUser = useAppSelector(getAuthUser);
  const allowToAddPermission =
    selectedUser &&
    !getValues("permissions").some(
      ({ user }: { user: UserDTO }) => user.id === selectedUser.id
    );

  const filteredAndSortedUsers = useMemo(() => {
    if (!users) {
      return [];
    }
    return sortByName(
      users.filter(
        (user) =>
          !RESERVED_USER_NAMES.includes(user.name) && user.id !== authUser?.id
      )
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
        helperText={errors.name?.message}
        placeholder={defaultValues?.name}
        InputLabelProps={
          // Allow to show placeholder when field is empty
          defaultValues?.name ? { shrink: true } : {}
        }
        fullWidth
        {...register("name", {
          required: t("form.field.required") as string,
          validate: (value) => {
            if (RESERVED_GROUP_NAMES.includes(value)) {
              return t("form.field.notAllowedValue") as string;
            }
          },
        })}
      />
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
              <FormControl sx={{ mr: 2, flex: 1 }} size="small">
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
                size="small"
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
                  <ListItemButton
                    sx={{ cursor: "default" }}
                    disableRipple
                    disableGutters
                  >
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
