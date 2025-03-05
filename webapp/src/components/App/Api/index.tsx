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

import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { getConfig } from "@/services/config";
import RootPage from "@/components/common/page/RootPage";
import { useTranslation } from "react-i18next";
import ApiIcon from "@mui/icons-material/Api";
import ViewWrapper from "../../common/page/ViewWrapper";
import "./styles.css";

function Api() {
  const { t } = useTranslation();

  return (
    <RootPage title={t("api.title")} titleIcon={ApiIcon}>
      <ViewWrapper>
        <SwaggerUI url={`${getConfig().downloadHostUrl}/openapi.json`} />
      </ViewWrapper>
    </RootPage>
  );
}

export default Api;
