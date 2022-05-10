/* eslint-disable react-hooks/exhaustive-deps */
import { PropsWithChildren, useState, useEffect } from "react";
import { Box, Button, CircularProgress, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { ConnectedProps, connect } from "react-redux";
import { useForm } from "react-hook-form";
import debug from "debug";
import { AppState } from "../../redux/ducks";
import { loginUser, logoutAction } from "../../redux/ducks/auth";
import {
  login as loginRequest,
  needAuth,
  refresh,
} from "../../services/api/auth";
import logo from "../../assets/logo.png";
import topRightBackground from "../../assets/top-right-background.png";
import GlobalPageLoadingError from "../../components/common/loaders/GlobalPageLoadingError";
import AppLoader from "../../components/common/loaders/AppLoader";
import { updateRefreshInterceptor } from "../../services/api/client";
import { UserInfo } from "../../common/types";
import { reconnectWebsocket } from "../../redux/ducks/websockets";
import FilledTextInput from "../../components/common/FilledTextInput";

const logError = debug("antares:loginwrapper:error");

type FormStatus = "loading" | "default" | "success";

interface Inputs {
  username: string;
  password: string;
}

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = {
  login: loginUser,
  logout: logoutAction,
  reconnectWs: reconnectWebsocket,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

function LoginWrapper(props: PropsWithChildren<PropTypes>) {
  const { register, handleSubmit, reset } = useForm<Inputs>();
  const [status, setStatus] = useState<FormStatus>("default");
  const [authRequired, setAuthRequired] = useState<boolean>();
  const [connexionError, setConnexionError] = useState(false);
  const [loginError, setLoginError] = useState<string>();
  const [t] = useTranslation();
  const { children } = props;
  const { user, login, logout, reconnectWs } = props;

  const onSubmit = async (data: Inputs) => {
    setStatus("loading");
    setLoginError("");
    setTimeout(async () => {
      try {
        const res = await loginRequest(data.username, data.password);
        setStatus("success");
        login(res);
      } catch (e) {
        setStatus("default");
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setLoginError((e as any).data?.message || t("main:loginError"));
      } finally {
        reset({ username: data.username });
      }
    }, 500);
  };

  useEffect(() => {
    (async () => {
      try {
        if (user) {
          updateRefreshInterceptor(async (): Promise<UserInfo | undefined> => {
            try {
              return refresh(user, login, logout);
            } catch (e) {
              logError("Failed to refresh token");
            }
            return undefined;
          });
        }
        const res = await needAuth();
        setAuthRequired(res);
      } catch (e) {
        setConnexionError(true);
      }
    })();
  }, [user]);

  useEffect(() => {
    if (authRequired !== undefined && !authRequired) {
      reconnectWs();
    }
  }, [authRequired]);

  if (authRequired === undefined) {
    return <AppLoader />;
  }

  if (connexionError) {
    return <GlobalPageLoadingError />;
  }

  if (user || !authRequired) {
    // eslint-disable-next-line react/jsx-no-useless-fragment
    return <>{children}</>;
  }

  return (
    <Box
      display="flex"
      height="100vh"
      sx={{
        background:
          "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
      }}
    >
      <Box
        position="absolute"
        top="0px"
        right="0px"
        display="flex"
        justifyContent="center"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <img src={topRightBackground} alt="logo" style={{ height: "auto" }} />
      </Box>
      <Box
        flexGrow={1}
        display="flex"
        alignItems="center"
        justifyContent="center"
        zIndex={999}
      >
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          flexDirection="column"
          flexWrap="nowrap"
          boxSizing="border-box"
        >
          <Box
            display="flex"
            width="70%"
            height="100%"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            flexWrap="nowrap"
            boxSizing="border-box"
          >
            <img src={logo} alt="logo" style={{ height: "96px" }} />
            <Typography variant="h4" component="h4" color="primary" my={2}>
              Antares Web
            </Typography>
          </Box>
          <Box width="70%" my={2}>
            <form
              style={{ marginTop: "16px" }}
              onSubmit={handleSubmit(onSubmit)}
            >
              <FilledTextInput
                label="NNI *"
                fullWidth
                inputProps={{ ...register("username", { required: true }) }}
                sx={{ my: 3 }}
              />
              <FilledTextInput
                type="password"
                label={t("main:password")}
                fullWidth
                inputProps={{ ...register("password", { required: true }) }}
              />
              {loginError && (
                <Box
                  mt={2}
                  color="error.main"
                  mb={4}
                  sx={{ fontSize: "0.9rem" }}
                >
                  {loginError}
                </Box>
              )}
              <Box display="flex" justifyContent="center" mt={6}>
                <Button
                  disabled={status === "loading"}
                  type="submit"
                  variant="contained"
                  color="primary"
                >
                  {status === "loading" && (
                    <CircularProgress size="1em" sx={{ mr: "1em" }} />
                  )}
                  {t("main:connexion")}
                </Button>
              </Box>
            </form>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default connector(LoginWrapper);
