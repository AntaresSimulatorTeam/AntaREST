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

//! Redux store must be imported before any redux ducks
import store from "../redux/store";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RegisteredRouter } from "@tanstack/react-router";
import { Provider } from "react-redux";
import InnerApp from "./InnerApp";

interface Props {
  queryClient: QueryClient;
  router: RegisteredRouter;
}

function App({ queryClient, router }: Props) {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <InnerApp router={router} />
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
