/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { useTranslation } from "react-i18next";

function General() {
  const { t } = useTranslation();

  return (
    <Form
      config={{
        defaultValues: {
          lang: getCurrentLanguage(),
        },
      }}
      onSubmit={({ dirtyValues }) => {
        if (dirtyValues.lang) {
          return changeLanguage(dirtyValues.lang);
        }
      }}
    >
      {({ control }) => (
        <Fieldset legend={t("global.language")}>
          <SelectFE
            name="lang"
            control={control}
            options={SUPPORTED_LANGUAGES.map((lang) => ({
              label: t(`lang.${lang}`),
              value: lang,
            }))}
            variant="outlined"
            size="small"
          />
        </Fieldset>
      )}
    </Form>
  );
}

export default General;
