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

import { createRouter, type LinkProps } from "@tanstack/react-router";
import type { U } from "ts-toolbelt";
import SimpleLoader from "./components/loaders/SimpleLoader";
import EmptyView from "./components/page/EmptyView";
import store from "./redux/store";
import { routeTree } from "./routeTree.gen";

const context = {
  auth: {
    isAuthenticated: false,
    isLoading: true,
    isRejected: false,
  },
  store,
};

export type RouterContext = typeof context;

const router = createRouter({
  routeTree,
  context,
  defaultPendingComponent: SimpleLoader,
  defaultErrorComponent: ({ error }) => <EmptyView title={error.toString()} />,
});

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

export type RoutePaths = U.Exclude<LinkProps["to"], undefined>;

export default router;
