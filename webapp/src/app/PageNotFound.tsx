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
import { useTranslation } from "react-i18next";

function PageNotFound() {
  const { t } = useTranslation();
  return (
    <EmptyView
      title={t("page.notFound")}
      icon={SearchOffIcon}
      action={
        <RouterButton to="/" variant="contained">
          {t("global.home")}
        </RouterButton>
      }
    />
  );
}

export default PageNotFound;
