/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { Box, keyframes, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import LoginIcon from "@mui/icons-material/Login";
import { login } from "../../../redux/ducks/auth";
import { needAuth } from "../../../services/api/auth";
import { getAuthUser } from "../../../redux/selectors";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import storage, { StorageKey } from "../../../services/utils/localStorage";
import Form from "../../common/Form";
import StringFE from "../../common/fieldEditors/StringFE";
import PasswordFE from "../../common/fieldEditors/PasswordFE";
import UsePromiseCond from "../../common/utils/UsePromiseCond";
import type { SubmitHandlerPlus } from "../../common/Form/types";
import Logo from "../../common/Logo";
import Wrapper from "./Wrapper";

const blinkAnimation = keyframes`
  50% {
    opacity: 0.4 
  }
`;

interface FormValues {
  username: string;
  password: string;
}

interface Props {
  children: React.ReactNode;
}

function Login(props: Props) {
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
      ifPending={() => (
        <Wrapper>
          <Logo size={80} pulse />
          <Box
            sx={{
              p: 2,
              span: {
                animation: `1s ${blinkAnimation} infinite`,
                ":nth-child(2)": {
                  animationDelay: "250ms",
                },
                ":nth-child(3)": {
                  animationDelay: "500ms",
                },
              },
            }}
          >
            {t("global.loading")}
            <Box component="span">.</Box>
            <Box component="span">.</Box>
            <Box component="span">.</Box>
          </Box>
        </Wrapper>
      )}
      ifRejected={() => (
        <Wrapper>
          <Typography variant="h4" sx={{ whiteSpace: "pre-wrap" }}>
            {t("login.error.message")}
          </Typography>
        </Wrapper>
      )}
      ifFulfilled={(canDisplayApp) => {
        if (canDisplayApp) {
          return children;
        }

        return (
          <Wrapper>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 2,
                mb: 2,
              }}
            >
              <Logo size={80} />
              <Typography
                variant="h5"
                sx={[
                  { color: "secondary.main" },
                  (theme) => theme.applyStyles("light", { color: "primary.main" }),
                ]}
              >
                Antares Web
              </Typography>
            </Box>
            <Box>
              <Form
                onSubmit={handleSubmit}
                submitButtonText={t("global.signIn")}
                submitButtonIcon={<LoginIcon />}
                hideFooterDivider
                sx={{
                  ".Form__Content": {
                    width: 250,
                  },
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
                      autoComplete="username"
                      id="username"
                      sx={{ mb: 1.5 }}
                      control={control}
                      rules={{ required: t("form.field.required") }}
                      fullWidth
                    />
                    <PasswordFE
                      name="password"
                      label={t("global.password")}
                      autoComplete="current-password"
                      id="current-password"
                      control={control}
                      rules={{ required: t("form.field.required") }}
                      fullWidth
                    />
                  </>
                )}
              </Form>
            </Box>
          </Wrapper>
        );
      }}
    />
  );
}

export default Login;
