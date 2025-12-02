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

import store from "@/redux/store";
import CloseIcon from "@mui/icons-material/Close";
import { Container, IconButton } from "@mui/material";
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { type SnackbarKey, SnackbarProvider, useSnackbar } from "notistack";
import { Provider } from "react-redux";
import ThemeProvider from "./-components/ThemeProvider";

function SnackbarCloseButton({ snackbarKey }: { snackbarKey: SnackbarKey }) {
  const { closeSnackbar } = useSnackbar();

  return (
    <IconButton onClick={() => closeSnackbar(snackbarKey)}>
      <CloseIcon />
    </IconButton>
  );
}

const RootLayout = () => (
  <>
    <Provider store={store}>
      <ThemeProvider>
        <SnackbarProvider
          maxSnack={5}
          autoHideDuration={3000}
          action={(key) => <SnackbarCloseButton snackbarKey={key} />}
          preventDuplicate
        >
          <Container>
            <Outlet />
          </Container>
        </SnackbarProvider>
      </ThemeProvider>
    </Provider>
    <TanStackRouterDevtools />
  </>
);

export const Route = createRootRoute({ component: RootLayout });
