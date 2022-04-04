/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { ConnectedProps, connect } from "react-redux";
import debug from "debug";
import { Box, Button, keyframes, styled, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import ErrorIcon from "@mui/icons-material/Error";
import { AppState } from "../../../store/reducers";
import { isUserAdmin } from "../../../services/utils";
import { getMaintenanceMode } from "../../../services/api/maintenance";
import { getConfig } from "../../../services/config";
import { setMaintenanceMode } from "../../../store/global";
import MessageInfoModal from "./MessageInfoModal";
import Stars from "./Stars";

const logError = debug("antares:maintenancewrapper:error");

const zoomEffect = keyframes`
0% { transform: scale(1.0) },
100% { transform: scale(1.05)}
`;

const StyledErrorIcon = styled(ErrorIcon)(({ theme }) => ({
  color: "white",
  width: "160px",
  height: "160px",
  animation: `${zoomEffect} 2s linear 0s infinite alternate`,
  marginRight: theme.spacing(5),
}));

const mapState = (state: AppState) => ({
  user: state.auth.user,
  maintenance: state.global.maintenanceMode,
});

const mapDispatch = {
  setMaintenance: setMaintenanceMode,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

function MaintenanceWrapper(props: PropsWithChildren<PropTypes>) {
  const [t] = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { children, user, maintenance, setMaintenance } = props;

  const onClick = () => {
    navigate("/login");
  };

  useEffect(() => {
    const init = async () => {
      const { maintenanceMode } = getConfig();
      try {
        const tmpMaintenance = await getMaintenanceMode();
        setMaintenance(tmpMaintenance);
      } catch (e) {
        logError(e);
        setMaintenance(maintenanceMode);
      }
    };
    init();
  }, []);

  if (
    maintenance &&
    (user === undefined || !isUserAdmin(user)) &&
    location.pathname !== "/login"
  ) {
    return (
      <Box
        display="flex"
        position="absolute"
        top="0px"
        left="0px"
        height="100vh"
        width="100vw"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        overflow="hidden"
        sx={{
          background:
            "linear-gradient(140deg, rgba(33,32,50,1) 0%, rgba(29,28,48,1) 35%, rgba(27,11,36,1) 100%)",
        }}
      >
        <Stars />
        <Button
          variant="text"
          sx={{
            color: "primary.main",
            position: "absolute",
            top: "10px",
            right: "10px",
          }}
          onClick={onClick}
        >
          {t("main:connexion")}
        </Button>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          zIndex={999}
        >
          <StyledErrorIcon />
          <Typography
            sx={{
              fontSize: "3.5em",
              fontWeight: "bold",
              color: "primary.main",
            }}
          >
            {t("main:appUnderMaintenance")}
            <br />
            {t("main:comeBackLater")}
          </Typography>
        </Box>
        <MessageInfoModal />
      </Box>
    );
  }

  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>{children}</>
  );
}

export default connector(MaintenanceWrapper);
