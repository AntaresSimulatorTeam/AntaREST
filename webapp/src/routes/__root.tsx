/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import DialogProvider from "@/components/dialogs/DialogProvider";
import type store from "@/redux/store";
import type { QueryClient } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { SnackbarProvider } from "notistack";
import SnackbarCloseButton from "./_authenticated/-components/SnackbarCloseButton";
import ThemeProvider from "./_authenticated/-components/ThemeProvider";

interface RouterContext {
  auth: {
    isAuthenticated: boolean;
    isLoading: boolean;
    isRejected: boolean;
  };
  store: typeof store;
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

const { VITE_ROUTER_DEVTOOLS, VITE_QUERY_DEVTOOLS } = import.meta.env;

function RootLayout() {
  return (
    <ThemeProvider>
      <SnackbarProvider
        maxSnack={5}
        autoHideDuration={3000}
        action={(key) => <SnackbarCloseButton snackbarKey={key} />}
        preventDuplicate
      >
        <DialogProvider>
          <Outlet />
        </DialogProvider>
      </SnackbarProvider>
      {VITE_ROUTER_DEVTOOLS === "true" && <TanStackRouterDevtools />}
      {VITE_QUERY_DEVTOOLS === "true" && <ReactQueryDevtools />}
    </ThemeProvider>
  );
}
