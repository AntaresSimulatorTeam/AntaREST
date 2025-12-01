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

import { useTranslation } from "react-i18next";
import {
  getMaintenanceMode,
  getMessageInfo,
  updateMaintenanceMode,
  updateMessageInfo,
} from "@/services/api/maintenance";
import Form from "@/components/common/Form";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import Fieldset from "@/components/common/Fieldset";

const getDefaultValues = async () => ({
  mode: await getMaintenanceMode(),
  message: await getMessageInfo(),
});

type DefaultValues = Awaited<ReturnType<typeof getDefaultValues>>;

function Maintenance() {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues: { mode, message } }: SubmitHandlerPlus<DefaultValues>) => {
    return Promise.all(
      [
        typeof mode === "boolean" && updateMaintenanceMode(mode),
        typeof message === "string" && updateMessageInfo(message),
      ].filter(Boolean),
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form config={{ defaultValues: getDefaultValues }} onSubmit={handleSubmit} enableUndoRedo>
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <SwitchFE name="mode" label={t("settings.maintenanceMode")} control={control} />
          <StringFE
            name="message"
            label={t("global.message")}
            control={control}
            minRows={6}
            multiline
          />
        </Fieldset>
      )}
    </Form>
  );
}

export default Maintenance;
