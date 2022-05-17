import { useEffect, useState } from "react";
import { Box, styled, Typography } from "@mui/material";
import { connect, ConnectedProps } from "react-redux";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { isStringEmpty, isUserAdmin } from "../../../services/utils";
import { getMessageInfo } from "../../../services/api/maintenance";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import OkDialog from "../../../components/common/dialogs/OkDialog";
import { AppState } from "../../../redux/ducks";
import { setMessageInfo } from "../../../redux/ducks/global";

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

const mapState = (state: AppState) => ({
  user: state.auth.user,
  messageInfo: state.global.messageInfo,
});

const mapDispatch = {
  setMessage: setMessageInfo,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function MessageInfoDialog(props: PropTypes) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { user, messageInfo, setMessage } = props;
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const tmpMessage = await getMessageInfo();
        setMessage(isStringEmpty(tmpMessage) ? "" : tmpMessage);
      } catch (e) {
        enqueueErrorSnackbar(t("main:onGetMessageInfoError"), e as AxiosError);
      }
    };
    init();
  }, [enqueueErrorSnackbar, setMessage, t]);

  useEffect(() => {
    if (
      messageInfo !== undefined &&
      messageInfo !== "" &&
      (user === undefined || !isUserAdmin(user))
    )
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

export default connector(MessageInfoDialog);
