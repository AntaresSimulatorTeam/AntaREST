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

import { ListItemButton } from "@mui/material";
import { createLink, type LinkComponent } from "@tanstack/react-router";

// Tanstack Router documentation:
// https://tanstack.com/router/latest/docs/framework/react/guide/custom-link#button

const CustomListItemButton = createLink(ListItemButton);

export const RouterListItemButton: LinkComponent<typeof ListItemButton> = (props) => {
  return <CustomListItemButton activeProps={{ selected: true }} {...props} />;
};

export default RouterListItemButton;
