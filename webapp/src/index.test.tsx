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

import { Provider } from "react-redux";

import { StyledEngineProvider } from "@mui/material";
import { render } from "@testing-library/react";

import App from "./components/App";
import store from "./redux/store";

describe("Application Render", () => {
  test("renders the App component with providers", () => {
    const { getByText } = render(
      <StyledEngineProvider injectFirst>
        <Provider store={store}>
          <App />
        </Provider>
      </StyledEngineProvider>,
    );

    expect(getByText("Antares Web")).toBeInTheDocument();
  });
});
