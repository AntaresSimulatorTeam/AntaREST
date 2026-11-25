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

import studiesReducer, { requestStudyFolderReveal } from "@/redux/ducks/studies";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import type { StudyMetadata } from "@/types/types";
import { createTheme, ThemeProvider } from "@mui/material";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import ExternalTree from "..";

const theme = createTheme({ cssVariables: true });

export function renderExternalTree({
  studies = [],
  initialPath,
}: {
  studies?: StudyMetadata[];
  initialPath?: string;
} = {}) {
  const store = configureStore({ reducer: { studies: studiesReducer } });

  if (initialPath) {
    store.dispatch(requestStudyFolderReveal({ tree: "external", path: initialPath }));
  }

  render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <ExternalTree studies={studies} onRootClick={vi.fn()} />
      </ThemeProvider>
    </Provider>,
    { wrapper: createQueryWrapper(createQueryClient()) },
  );

  return store;
}

export function treeItem(name: string) {
  return screen.getByRole("treeitem", { name });
}
