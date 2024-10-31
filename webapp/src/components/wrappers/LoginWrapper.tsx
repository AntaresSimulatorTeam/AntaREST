/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import LoginIcon from "@mui/icons-material/Login";
import { login } from "@/redux/ducks/auth";
import logo from "@/assets/img/logo.png";
import topRightBackground from "@/assets/img/top-right-background.png";
import GlobalPageLoadingError from "../common/loaders/GlobalPageLoadingError";
import AppLoader from "../common/loaders/AppLoader";
import { needAuth } from "@/services/api/auth";
import { getAuthUser } from "@/redux/selectors";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useAppSelector from "@/redux/hooks/useAppSelector";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import storage, { StorageKey } from "@/services/utils/localStorage";
import Form from "../common/Form";
import StringFE from "../common/fieldEditors/StringFE";
import PasswordFE from "../common/fieldEditors/PasswordFE";
import UsePromiseCond from "../common/utils/UsePromiseCond";
import { SubmitHandlerPlus } from "../common/Form/types";

interface FormValues {
  username: string;
  password: string;
}

interface Props {
  children: React.ReactNode;
}

function LoginWrapper(props: Props) {
  const { children } = props;
  const { t } = useTranslation();
  const user = useAppSelector(getAuthUser);
  const dispatch = useAppDispatch();

  const res = usePromiseWithSnackbarError(
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
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<FormValues>) => {
    return dispatch(login(values)).unwrap();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifPending={() => <AppLoader />}
      ifRejected={() => <GlobalPageLoadingError />}
      ifResolved={(canDisplayApp) =>
        canDisplayApp ? (
          children
        ) : (
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
              <img
                src={topRightBackground}
                alt="logo"
                style={{ height: "auto" }}
              />
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
                  <Typography
                    variant="h4"
                    component="h4"
                    color="primary"
                    my={2}
                  >
                    Antares Web
                  </Typography>
                </Box>
                <Box width="70%" my={2}>
                  <Form
                    onSubmit={handleSubmit}
                    submitButtonText={t("global.connexion")}
                    submitButtonIcon={<LoginIcon />}
                    hideFooterDivider
                    sx={{
                      ".Form__Footer__Actions": {
                        justifyContent: "center",
                      },
                    }}
                  >
                    {({ control }) => (
                      <>
                        <StringFE
                          name="username"
                          label="NNI"
                          variant="filled"
                          size="small"
                          sx={{ mb: 2 }}
                          fullWidth
                          control={control}
                          rules={{ required: t("form.field.required") }}
                        />
                        <PasswordFE
                          name="password"
                          label={t("global.password")}
                          variant="filled"
                          size="small"
                          inputProps={{
                            // https://web.dev/sign-in-form-best-practices/#current-password
                            autoComplete: "current-password",
                            id: "current-password",
                          }}
                          sx={{ mb: 3 }}
                          fullWidth
                          control={control}
                          rules={{ required: t("form.field.required") }}
                        />
                      </>
                    )}
                  </Form>
                </Box>
              </Box>
            </Box>
          </Box>
        )
      }
    />
  );
}

export default LoginWrapper;
