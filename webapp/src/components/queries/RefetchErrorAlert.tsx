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

import { Alert, AlertTitle } from "@mui/material";
import { useTranslation } from "react-i18next";

export interface RefetchErrorAlertProps {
  isRefetchError: boolean;
  error: Error | null;
}

function RefetchErrorAlert({ isRefetchError, error }: RefetchErrorAlertProps) {
  const { t } = useTranslation();

  if (!isRefetchError) {
    return null;
  }

  return (
    <Alert severity="error" sx={{ mb: 1 }}>
      <AlertTitle>{t("query.error.refetch")}</AlertTitle>
      {error?.message}
    </Alert>
  );
}

export default RefetchErrorAlert;
