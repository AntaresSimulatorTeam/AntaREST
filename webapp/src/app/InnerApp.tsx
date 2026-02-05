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

import { useQueryClient } from "@tanstack/react-query";
import { RouterProvider, type RegisteredRouter } from "@tanstack/react-router";
import { useEffect } from "react";
import useAuth from "./useAuth";

interface Props {
  router: RegisteredRouter;
}

function InnerApp({ router }: Props) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  useEffect(() => {
    // cf. https://github.com/TanStack/router/issues/1604#issuecomment-2118648159
    router.invalidate();
  }, [auth, router]);

  return <RouterProvider router={router} context={{ auth, queryClient }} />;
}

export default InnerApp;
