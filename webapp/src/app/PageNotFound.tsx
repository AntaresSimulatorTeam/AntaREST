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

import EmptyView from "@/components/page/EmptyView";
import RouterButton from "@/components/router/RouterButton";
import SearchOffIcon from "@mui/icons-material/SearchOff";
import { useMatch } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function PageNotFound() {
  const { t } = useTranslation();
  const match = useMatch({ strict: false });
  const isRoot = match.routeId === "__root__";

  // In the root route, there is no menu to go back
  const actions = isRoot ? (
    <RouterButton to={location.pathname.split("/").slice(0, -1).join("/")} variant="contained">
      {t("global.home")}
    </RouterButton>
  ) : null;

  return <EmptyView title={t("page.notFound")} icon={SearchOffIcon} actions={actions} />;
}

export default PageNotFound;
