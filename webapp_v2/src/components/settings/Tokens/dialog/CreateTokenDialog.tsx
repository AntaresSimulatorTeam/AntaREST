import TokenIcon from "@mui/icons-material/Token";
import { IconButton, Paper, Tooltip, Typography } from "@mui/material";
import { group } from "console";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  BotCreateDTO,
  BotDetailsDTO,
  BotDTO,
  BotRoleCreateDTO,
  GroupDTO,
  RoleType,
} from "../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { createBot } from "../../../../services/api/user";
import { SubmitHandlerData } from "../../../common/dialogs/FormDialog";
import OkDialog from "../../../common/dialogs/OkDialog";
import TokenFormDialog, { TokenFormDialogProps } from "./TokenFormDialog";

/**
 * Types
 */

type InheritPropsToOmit = "title" | "titleIcon" | "onSubmit" | "onCancel";

interface Props extends Omit<TokenFormDialogProps, InheritPropsToOmit> {
  addToken: (token: BotDTO) => void;
  reloadFetchTokens: VoidFunction;
  closeDialog: VoidFunction;
}

/**
 * Component
 */

function CreateTokenDialog(props: Props) {
  const { addToken, reloadFetchTokens, closeDialog, ...dialogProps } = props;
  const [tokenValueToDisplay, setTokenValueToDisplay] = useState("");
  const [showCopiedTooltip, setShowCopiedTooltip] = useState(false);
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { name, linkToUser, permissions } = data.values;

    try {
      const roles = permissions.map(
        (perm: { group: GroupDTO; type: RoleType }) => ({
          group: perm.group.id,
          role: perm.type,
        })
      ) as BotCreateDTO["roles"];

      const tokenValue = await mounted(
        createBot({ name, is_author: linkToUser, roles })
      );

      setTokenValueToDisplay(tokenValue);

      // TODO
      // addToken({ });

      enqueueSnackbar(t("settings:onTokenCreation", [name]), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("settings:onTokenSaveError", [name]), e as Error);
      closeDialog();
    } finally {
      reloadFetchTokens();
    }
  };

  const handleCopyClick = () => {
    navigator.clipboard
      .writeText(tokenValueToDisplay)
      .then(() => setShowCopiedTooltip(true));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <TokenFormDialog
        title={t("settings:createToken")}
        titleIcon={TokenIcon}
        onSubmit={handleSubmit}
        onCancel={closeDialog}
        {...dialogProps}
      />
      {tokenValueToDisplay && (
        <OkDialog
          open
          title={t("settings:printTokenMessage") as string}
          onOk={() => {
            setTokenValueToDisplay("");
            closeDialog();
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 2,
              pb: 6,
              position: "relative",
              overflowWrap: "break-word",
              backgroundImage:
                "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
            }}
          >
            {tokenValueToDisplay}
            <IconButton
              sx={{ position: "absolute", right: 3, bottom: 3 }}
              size="large"
            >
              <Tooltip
                open={showCopiedTooltip}
                PopperProps={{
                  disablePortal: true,
                }}
                onClose={() => setShowCopiedTooltip(false)}
                disableFocusListener
                disableHoverListener
                disableTouchListener
                title={t("settings:tokenCopied") as string}
              >
                <ContentCopyIcon onClick={handleCopyClick} />
              </Tooltip>
            </IconButton>
          </Paper>
        </OkDialog>
      )}
    </>
  );
}

export default CreateTokenDialog;
