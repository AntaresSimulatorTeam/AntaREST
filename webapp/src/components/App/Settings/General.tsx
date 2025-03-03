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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import Fieldset from "@/components/common/Fieldset";
import Form from "@/components/common/Form";
import { SUPPORTED_LANGUAGES } from "@/i18n";
import { changeLanguage, getCurrentLanguage } from "@/utils/i18nUtils";
import { useColorScheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { THEME_MODES } from "../shared/constants";

function General() {
  const { mode, setMode } = useColorScheme();
  const { t } = useTranslation();

  const defaultValues = {
    lang: getCurrentLanguage(),
    themeMode: mode,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<typeof defaultValues>) => {
    if (dirtyValues.themeMode) {
      setMode(dirtyValues.themeMode);
    }

    if (dirtyValues.lang) {
      return changeLanguage(dirtyValues.lang);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form config={{ defaultValues }} onSubmit={handleSubmit}>
      {({ control }) => (
        <>
          <Fieldset>
            <SelectFE
              label={t("global.language")}
              name="lang"
              control={control}
              options={SUPPORTED_LANGUAGES.map((lang) => ({
                label: t(`lang.${lang}`),
                value: lang,
              }))}
              variant="outlined"
            />
            <SelectFE
              label={t("global.theme")}
              name="themeMode"
              control={control}
              options={THEME_MODES.map((option) => ({
                ...option,
                label: t(`global.${option.value}`),
              }))}
              variant="outlined"
            />
          </Fieldset>
        </>
      )}
    </Form>
  );
}

export default General;
