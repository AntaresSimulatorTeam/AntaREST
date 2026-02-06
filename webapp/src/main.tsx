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

import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import PageNotFound from "./app/PageNotFound";
import SimpleLoader from "./components/loaders/SimpleLoader";
import ErrorView from "./components/page/ErrorView";
import store from "./redux/store";
import { routeTree } from "./routeTree.gen";
import { initConfig } from "./services/config";

if (import.meta.env.DEV) {
  // Remove message from Emotion library about unsafe usage in SSR
  const originalError = console.error;
  console.error = (message, ...rest) => {
    if (
      typeof message === "string" &&
      message.includes("unsafe when doing server-side rendering")
    ) {
      return;
    }
    originalError(message, ...rest);
  };
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
    },
  },
});

const router = createRouter({
  routeTree,
  context: {
    auth: {
      isAuthenticated: false,
      isLoading: true,
      isRejected: false,
    },
    store,
    queryClient,
  },
  defaultPendingComponent: SimpleLoader,
  defaultErrorComponent: ErrorView,
  defaultNotFoundComponent: PageNotFound,
});

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

initConfig().then(() => {
  const rootContainer = document.getElementById("root");

  if (!rootContainer) {
    throw new Error("Root container not found");
  }

  createRoot(rootContainer).render(<App queryClient={queryClient} router={router} />);
});
