import { useEffect, useState } from "react";
import { Box, styled, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { isStringEmpty, isUserAdmin } from "../../../services/utils";
import { getMessageInfo as getMessageInfoAPI } from "../../../services/api/maintenance";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import OkDialog from "../../../components/common/dialogs/OkDialog";
import { setMessageInfo } from "../../../redux/ducks/ui";
import { useAppDispatch, useAppSelector } from "../../../redux/hooks";
import { getAuthUser, getMessageInfo } from "../../../redux/selectors";

export const Main = styled(Box)(({ theme }) => ({
  width: "600px",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  padding: theme.spacing(2),
  marginBottom: theme.spacing(3),
  boxSizing: "border-box",
}));

function MessageInfoDialog() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [open, setOpen] = useState(false);
  const user = useAppSelector(getAuthUser);
  const messageInfo = useAppSelector(getMessageInfo);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const init = async () => {
      try {
        const tmpMessage = await getMessageInfoAPI();
        dispatch(setMessageInfo(isStringEmpty(tmpMessage) ? "" : tmpMessage));
      } catch (e) {
        enqueueErrorSnackbar(
          t("maintenance.error.messageInfoError"),
          e as AxiosError
        );
      }
    };
    init();
  }, [dispatch, enqueueErrorSnackbar, t]);

  useEffect(() => {
    if (messageInfo && (user === undefined || !isUserAdmin(user)))
      setOpen(true);
  }, [messageInfo, user]);

  return (
    <OkDialog
      open={open}
      title="Information"
      contentProps={{
        sx: { width: "100%", height: "auto", p: 0 },
      }}
      onOk={() => setOpen(false)}
    >
      <Main>
        <Typography variant="body1" style={{ whiteSpace: "pre-wrap" }}>
          {messageInfo}
        </Typography>
      </Main>
    </OkDialog>
  );
}

export default MessageInfoDialog;
