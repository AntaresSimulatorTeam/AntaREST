import { ReactNode, useState } from "react";
import { Box, Button, CircularProgress, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { SubmitHandler, useForm } from "react-hook-form";
import { login, refresh } from "../../redux/ducks/auth";
import logo from "../../assets/logo.png";
import topRightBackground from "../../assets/top-right-background.png";
import GlobalPageLoadingError from "../../components/common/loaders/GlobalPageLoadingError";
import AppLoader from "../../components/common/loaders/AppLoader";
import FilledTextInput from "../../components/common/FilledTextInput";
import { needAuth } from "../../services/api/auth";
import { getAuthUser } from "../../redux/selectors";
import usePromiseWithSnackbarError from "../../hooks/usePromiseWithSnackbarError";
import { isUserExpired } from "../../services/utils";
import { initWebSocket } from "../../services/webSockets";
import { useAppDispatch, useAppSelector } from "../../redux/hooks";

interface Inputs {
  username: string;
  password: string;
}

interface Props {
  children: ReactNode;
}

function LoginWrapper(props: Props) {
  const { children } = props;
  const { register, handleSubmit, reset, formState } = useForm<Inputs>();
  const [loginError, setLoginError] = useState("");
  const { t } = useTranslation();
  const user = useAppSelector(getAuthUser);
  const dispatch = useAppDispatch();

  const {
    data: canDisplayApp,
    isLoading,
    isRejected,
  } = usePromiseWithSnackbarError(
    async () => {
      const isAuthNeeded = await needAuth();
      if (!isAuthNeeded) {
        initWebSocket(dispatch);
        return true;
      }
      if (user) {
        if (isUserExpired(user)) {
          await dispatch(refresh()).unwrap();
        }
        return true;
      }
      return false;
    },
    {
      errorMessage: t("main:loginError"),
    },
    [user]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLoginSubmit: SubmitHandler<Inputs> = async (data) => {
    setLoginError("");
    setTimeout(async () => {
      try {
        await dispatch(login(data)).unwrap();
      } catch (e) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setLoginError((e as any).data?.message || t("global:login.error"));
      } finally {
        reset({ username: data.username });
      }
    }, 500);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isLoading) {
    return <AppLoader />;
  }

  if (isRejected) {
    return <GlobalPageLoadingError />;
  }

  if (canDisplayApp) {
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
              onSubmit={handleSubmit(handleLoginSubmit)}
            >
              <FilledTextInput
                label="NNI *"
                fullWidth
                inputProps={{ ...register("username", { required: true }) }}
                sx={{ my: 3 }}
              />
              <FilledTextInput
                type="password"
                label={t("global:global.password")}
                fullWidth
                inputProps={{
                  autoComplete: "current-password",
                  ...register("password", { required: true }),
                }}
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
                  disabled={formState.isSubmitting}
                  type="submit"
                  variant="contained"
                  color="primary"
                >
                  {formState.isSubmitting && (
                    <CircularProgress size="1em" sx={{ mr: "1em" }} />
                  )}
                  {t("global:global.connexion")}
                </Button>
              </Box>
            </form>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default LoginWrapper;
