import { DialogContentText } from "@mui/material";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import InfoIcon from "@mui/icons-material/Info";
import { useMemo } from "react";
import { BotDetailsDTO, RoleType, UserDTO } from "../../../../../common/types";
import OkDialog, { OkDialogProps } from "../../../../common/dialogs/OkDialog";
import TokenForm from "./TokenFormDialog/TokenForm";

/**
 * Types
 */

interface Props extends Omit<OkDialogProps, "title" | "titleIcon"> {
  token: BotDetailsDTO;
}

type DefaultValuesType = {
  permissions?: Array<{ user: UserDTO; type: RoleType }>;
};

/**
 * Component
 */

function TokenInfoDialog(props: Props) {
  const { token, ...dialogProps } = props;

  const defaultValues = useMemo(
    () => ({
      name: token.name,
      permissions: token.roles.map((role) => ({
        group: {
          id: role.group_id,
          name: role.group_name,
        },
        type: role.type,
      })),
    }),
    [token]
  );

  const formObj = useForm<DefaultValuesType>({ defaultValues });
  const { t } = useTranslation();

  return (
    <OkDialog
      maxWidth="sm"
      fullWidth
      {...dialogProps}
      title={t("global.permissions")}
      titleIcon={InfoIcon}
    >
      <DialogContentText>
        {t("settings.currentToken", [token.name])}
      </DialogContentText>
      <TokenForm onlyPermissions readOnly {...formObj} />
    </OkDialog>
  );
}

export default TokenInfoDialog;
