import { ReactNode, useState } from "react";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";
import { login } from "../../redux/ducks/auth";
import logo from "../../assets/logo.png";
import topRightBackground from "../../assets/top-right-background.png";
import GlobalPageLoadingError from "../common/loaders/GlobalPageLoadingError";
import AppLoader from "../common/loaders/AppLoader";
import { needAuth } from "../../services/api/auth";
import { getAuthUser } from "../../redux/selectors";
import usePromiseWithSnackbarError from "../../hooks/usePromiseWithSnackbarError";
import useAppSelector from "../../redux/hooks/useAppSelector";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import storage, { StorageKey } from "../../services/utils/localStorage";
import Form, { SubmitHandlerPlus } from "../common/Form";
import StringFE from "../common/fieldEditors/StringFE";
import PasswordFE from "../common/fieldEditors/PasswordFE";

interface FormValues {
  username: string;
  password: string;
}

interface Props {
  children: ReactNode;
}

function LoginWrapper(props: Props) {
  const { children } = props;
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
      if (user) {
        return true;
      }
      if (!(await needAuth())) {
        await dispatch(login());
        return true;
      }
      const userFromStorage = storage.getItem(StorageKey.AuthUser);
      if (userFromStorage) {
        await dispatch(login(userFromStorage));
        return true;
      }
      return false;
    },
    {
      errorMessage: t("login.error"),
      resetDataOnReload: false,
      deps: [user],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<FormValues>) => {
    const { values } = data;

    setLoginError("");

    try {
      await dispatch(login(values)).unwrap();
    } catch (err) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setLoginError((err as any).data?.message || t("login.error"));
      throw err;
    }
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
            <Form onSubmit={handleSubmit} hideSubmitButton>
              {({ control, formState: { isDirty, isSubmitting } }) => (
                <>
                  <StringFE
                    name="username"
                    sx={{ my: 3 }}
                    label="NNI"
                    variant="filled"
                    fullWidth
                    control={control}
                    rules={{ required: t("form.field.required") }}
                  />
                  <PasswordFE
                    name="password"
                    variant="filled"
                    label={t("global.password")}
                    inputProps={{ autoComplete: "current-password" }}
                    fullWidth
                    control={control}
                    rules={{ required: t("form.field.required") }}
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
                    <LoadingButton
                      type="submit"
                      variant="contained"
                      loading={isSubmitting}
                      disabled={!isDirty || isSubmitting}
                    >
                      {t("global.connexion")}
                    </LoadingButton>
                  </Box>
                </>
              )}
            </Form>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default LoginWrapper;
