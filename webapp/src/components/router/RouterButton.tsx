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

import { Button } from "@mui/material";
import { createLink } from "@tanstack/react-router";

// Tanstack Router documentation:
// https://tanstack.com/router/latest/docs/framework/react/guide/custom-link#button
// https://tanstack.com/router/latest/docs/framework/react/how-to/integrate-material-ui#step-2-create-typed-mui-button-component

const RouterButton = createLink(Button);

export default RouterButton;
