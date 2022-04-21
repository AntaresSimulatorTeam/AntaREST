import { useTranslation } from "react-i18next";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import { MouseEventHandler, useMemo, useRef, useState } from "react";
import {
  TextField,
  Container,
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
import { FieldValues, SubmitHandler, useFieldArray } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { v4 as uuidv4 } from "uuid";
import DeleteIcon from "@mui/icons-material/Delete";
import GroupWorkIcon from "@mui/icons-material/GroupWork";
import * as RA from "ramda-adjunct";
import { RESERVED_GROUP_NAMES, RESERVED_USER_NAMES, sortByName } from "./utils";
import FormDialog, { FormObj } from "../../common/dialogs/FormDialog";
import { GroupDTO, RoleType } from "../../../common/types";
import { roleToString } from "../../../services/utils";
import { scrollbarStyle } from "../../../theme";
import usePromise from "../../../hooks/usePromise";
import { getGroups } from "../../../services/api/user";

/**
 * Types
 */

interface Props {
  open: boolean;
  onSubmit: SubmitHandler<FieldValues>;
  onCancel: MouseEventHandler<HTMLButtonElement>;
}

/**
 * Constants
 */

// TODO: translate error messages
const schema = yup.object({
  username: yup.string().required().notOneOf(RESERVED_USER_NAMES),
  password: yup.string().min(8).required(),
});

const roleTypeKeys = Object.values(RoleType).filter(
  RA.isString
) as (keyof typeof RoleType)[];

/**
 * Components
 */

function CreateUserDialog(props: Props) {
  const { t } = useTranslation();

  return (
    <FormDialog
      maxWidth="sm"
      formOptions={{
        mode: "onTouched",
        resolver: yupResolver(schema),
      }}
      title={t("settings:newUserTitle")}
      titleIcon={PersonAddAltIcon}
      {...props}
    >
      {UserForm}
    </FormDialog>
  );
}

function UserForm(props: FormObj) {
  const {
    control,
    register,
    getValues,
    formState: { errors },
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
    sx: { mx: 0 },
    fullWidth: true,
    required: true,
  };
  const allowToAddRole =
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
    const group = groups?.find((group) => group.id === groupId);
    setSelectedGroup(group);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Container sx={{ py: 1 }}>
      {/* Login credentials */}
      <TextField
        label={t("settings:usernameLabel")}
        error={!!errors.username}
        helperText={errors.username?.message}
        {...commonTextFieldProps}
        {...register("username")}
      />
      <TextField
        label={t("settings:passwordLabel")}
        type="password"
        error={!!errors.password}
        helperText={errors.password?.message}
        {...commonTextFieldProps}
        {...register("password")}
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
        <Typography>{t("settings:permissionsLabel")}</Typography>
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
        {groups && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
              <FormControl sx={{ mr: 2, flex: 1 }} size="small">
                <InputLabel id={groupLabelId}>{t("settings:group")}</InputLabel>
                <Select
                  labelId={groupLabelId}
                  label={t("settings:group")}
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
                disabled={!allowToAddRole}
                onClick={() => {
                  append({
                    group: selectedGroup,
                    // Allow to force number, `defaultValue` alone gives a string.
                    type: RoleType.READER,
                  });
                }}
              >
                {t("settings:addButton")}
              </Button>
            </Box>
            <List
              sx={{
                ...scrollbarStyle,
                maxHeight: "300px",
                overflow: "auto",
              }}
            >
              {fields.map((field, index) => (
                <ListItem
                  key={field.id}
                  secondaryAction={
                    <>
                      <Select
                        defaultValue={RoleType.READER}
                        variant="standard"
                        {...register(`permissions.${index}.type`)}
                      >
                        {roleTypeKeys.map((key) => (
                          <MenuItem key={key} value={RoleType[key]}>
                            {roleToString(RoleType[key])}
                          </MenuItem>
                        ))}
                      </Select>
                      <IconButton edge="end" onClick={() => remove(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </>
                  }
                  disablePadding
                  dense
                >
                  <ListItemButton disableGutters>
                    <ListItemIcon sx={{ minWidth: 0, p: "0 15px 0 5px" }}>
                      <GroupWorkIcon />
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
    </Container>
  );
}

export default CreateUserDialog;
