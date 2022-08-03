import { DialogContentText } from "@mui/material";
import { useTranslation } from "react-i18next";
import InfoIcon from "@mui/icons-material/Info";
import { useMemo } from "react";
import { FieldValues } from "react-hook-form";
import { BotDetailsDTO, GroupDTO, RoleType } from "../../../../../common/types";
import OkDialog, { OkDialogProps } from "../../../../common/dialogs/OkDialog";
import TokenForm from "./TokenFormDialog/TokenForm";
import Form from "../../../../common/Form";

/**
 * Types
 */

interface Props extends Omit<OkDialogProps, "title" | "titleIcon"> {
  token: BotDetailsDTO;
}

/**
 * Component
 */

function TokenInfoDialog(props: Props) {
  const { token, ...dialogProps } = props;

  // TODO: FieldValues is used to fix an issue with TokenForm
  const defaultValues = useMemo<FieldValues>(
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
      <Form config={{ defaultValues }} hideSubmitButton>
        {(formObj) => <TokenForm onlyPermissions readOnly {...formObj} />}
      </Form>
    </OkDialog>
  );
}

export default TokenInfoDialog;
