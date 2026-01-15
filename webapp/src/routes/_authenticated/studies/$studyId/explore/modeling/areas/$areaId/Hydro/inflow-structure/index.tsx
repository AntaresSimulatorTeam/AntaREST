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

import NumberFE from "@/components/fieldEditors/NumberFE";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  type InflowStructureFields,
  getInflowStructureFields,
  updateInflowStructureFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/inflow-structure/",
)({
  component: InflowStructure,
});

function InflowStructure() {
  const { studyId, areaId } = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<InflowStructureFields>) => {
    return updateInflowStructureFields(studyId, areaId, data.values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={areaId}
      config={{
        defaultValues: () => getInflowStructureFields(studyId, areaId),
      }}
      onSubmit={handleSubmit}
      miniSubmitButton
      enableUndoRedo
      hideFooterDivider
      disableStickyFooter
      sx={{
        flexDirection: "row",
        alignItems: "center",
        gap: 1,
        overflow: "hidden",
        ".Form__Footer": {
          mt: 0,
        },
      }}
    >
      {({ control }) => (
        <NumberFE
          label="Inter-Monthly Correlation"
          name="interMonthlyCorrelation"
          control={control}
          rules={{
            min: {
              value: 0,
              message: t("form.field.minValue", { 0: 0 }),
            },
            max: {
              value: 1,
              message: t("form.field.maxValue", { 0: 1 }),
            },
          }}
          slotProps={{ htmlInput: { step: 0.1 } }}
          size="extra-small"
          margin="dense"
        />
      )}
    </Form>
  );
}
