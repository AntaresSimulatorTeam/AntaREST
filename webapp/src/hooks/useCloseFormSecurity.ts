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

import usePrompt from "./usePrompt";
import { useTranslation } from "react-i18next";

export interface UseFormCloseProtectionParams {
  isSubmitting: boolean;
  isDirty: boolean;
}

function useFormCloseProtection({ isSubmitting, isDirty }: UseFormCloseProtectionParams) {
  const { t } = useTranslation();

  usePrompt(t("form.submit.inProgress"), isSubmitting);
  usePrompt(t("form.changeNotSaved"), isDirty && !isSubmitting);
}

export default useFormCloseProtection;
