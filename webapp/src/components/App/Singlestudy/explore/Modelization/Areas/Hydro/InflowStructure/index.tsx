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

import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";

import { StudyMetadata } from "@/common/types";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import Form from "@/components/common/Form";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentAreaId } from "@/redux/selectors";

import {
  getInflowStructureFields,
  type InflowStructureFields,
  updateInflowStructureFields,
} from "./utils";

function InflowStructure() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<InflowStructureFields>) => {
    return updateInflowStructureFields(study.id, areaId, data.values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id + areaId}
      config={{
        defaultValues: () => getInflowStructureFields(study.id, areaId),
      }}
      onSubmit={handleSubmit}
      miniSubmitButton
      enableUndoRedo
      hideFooterDivider
      sx={{ flexDirection: "row", alignItems: "center" }}
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
          inputProps={{ step: 0.1 }}
          size="small"
          sx={{ width: 180 }}
        />
      )}
    </Form>
  );
}

export default InflowStructure;
