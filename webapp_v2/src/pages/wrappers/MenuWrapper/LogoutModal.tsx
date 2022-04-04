import React from "react";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
import BasicModal from "../../../components/common/BasicModal";
import { AppState } from "../../../store/reducers";
import { logoutAction } from "../../../store/auth";

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = {
  logout: logoutAction,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  open: boolean;
  onClose: () => void;
}
type PropTypes = PropsFromRedux & OwnProps;

function LogoutModal(props: PropTypes) {
  const [t] = useTranslation();
  const { logout, open, onClose } = props;

  return (
    <BasicModal
      title={t("main:logout")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:noButton")}
      actionButtonLabel={t("main:yesButton")}
      onActionButtonClick={logout}
      rootStyle={{
        width: "600px",
        height: "200px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        width="100%"
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        p={2}
        boxSizing="border-box"
      >
        <Typography>{t("main:logoutModalMessage")}</Typography>
      </Box>
    </BasicModal>
  );
}

export default connector(LogoutModal);
