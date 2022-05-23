/* eslint-disable react-hooks/exhaustive-deps */
import { ReactNode, useEffect } from "react";
import { useTranslation } from "react-i18next";
import debug from "debug";
import { Box, Button, keyframes, styled, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import ErrorIcon from "@mui/icons-material/Error";
import { isUserAdmin } from "../../../services/utils";
import { getConfig } from "../../../services/config";
import MessageInfoDialog from "./MessageInfoDialog";
import Stars from "./Stars";
import { setMaintenanceMode } from "../../../redux/ducks/ui";
import { useAppDispatch, useAppSelector } from "../../../redux/hooks";
import { getAuthUser, getMaintenanceMode } from "../../../redux/selectors";
import { getMaintenanceMode as getMaintenanceModeAPI } from "../../../services/api/maintenance";

const logError = debug("antares:maintenancewrapper:error");

const zoomEffect = keyframes`
  0% { 
    transform: scale(1.0) 
  }
  100% { 
    transform: scale(1.05)
  }
`;

const StyledErrorIcon = styled(ErrorIcon)(({ theme }) => ({
  color: "white",
  width: "160px",
  height: "160px",
  animation: `${zoomEffect} 2s linear 0s infinite alternate`,
  marginRight: theme.spacing(5),
}));

interface Props {
  children: ReactNode;
}

function MaintenanceWrapper(props: Props) {
  const { children } = props;
  const [t] = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAppSelector(getAuthUser);
  const maintenanceMode = useAppSelector(getMaintenanceMode);
  const dispatch = useAppDispatch();

  const onClick = () => {
    navigate("/login");
  };

  useEffect(() => {
    const init = async () => {
      try {
        const tmpMaintenance = await getMaintenanceModeAPI();
        dispatch(setMaintenanceMode(tmpMaintenance));
      } catch (e) {
        logError(e);
        dispatch(setMaintenanceMode(getConfig().maintenanceMode));
      }
    };
    init();
  }, []);

  if (
    maintenanceMode &&
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
            "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
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
          {t("global.connexion")}
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
            {t("maintenance.message.underMaintenance")}
            <br />
            {t("maintenance.message.comeBackLater")}
          </Typography>
        </Box>
        <MessageInfoDialog />
      </Box>
    );
  }

  return (
    <>
      {children}
      <MessageInfoDialog />
    </>
  );
}

export default MaintenanceWrapper;
