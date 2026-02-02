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

import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import EmptyView, { type EmptyViewProps } from "./EmptyView";

interface ErrorViewProps extends Omit<EmptyViewProps, "title" | "icon"> {
  error: Error | string;
}

function ErrorView({ error, ...rest }: ErrorViewProps) {
  const title = typeof error === "string" ? error : error.message;
  return <EmptyView {...rest} title={title} icon={ErrorOutlineIcon} />;
}

export default ErrorView;
