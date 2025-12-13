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

import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import Logo from "@/components/Logo";
import PasswordFE from "@/components/fieldEditors/PasswordFE";
import StringFE from "@/components/fieldEditors/StringFE";
import LoginIcon from "@mui/icons-material/Login";
import { Box, keyframes, Typography } from "@mui/material";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { login } from "../../redux/ducks/auth";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import Wrapper from "./-components/Wrapper";

export const Route = createFileRoute("/login/")({
  validateSearch: (search) => ({
    // `search.redirect` from '_authenticated' route
    redirect: (search.redirect as string) || "/",
  }),
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({ to: search.redirect });
    }
  },
  component: Login,
});

const blinkAnimation = keyframes`
  50% {
    opacity: 0.4 
  }
`;

interface FormValues {
  username: string;
  password: string;
}

function Login() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { auth } = Route.useRouteContext();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<FormValues>) => {
    return dispatch(login(values)).unwrap();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (auth.isLoading) {
    return (
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
    );
  }

  if (auth.isRejected) {
    return (
      <Wrapper>
        <Typography variant="h4" sx={{ whiteSpace: "pre-wrap" }}>
          {t("login.error.message")}
        </Typography>
      </Wrapper>
    );
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
          disableBlocker
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
            <Fieldset fullFieldWidth>
              <StringFE
                name="username"
                label="NNI"
                autoComplete="username"
                id="username"
                control={control}
                rules={{ required: t("form.field.required") }}
              />
              <PasswordFE
                name="password"
                label={t("global.password")}
                autoComplete="current-password"
                id="current-password"
                control={control}
                rules={{ required: t("form.field.required") }}
              />
            </Fieldset>
          )}
        </Form>
      </Box>
    </Wrapper>
  );
}
