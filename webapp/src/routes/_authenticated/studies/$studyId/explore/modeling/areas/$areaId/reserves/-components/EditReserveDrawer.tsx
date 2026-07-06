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

import FormDrawer from "@/components/FormDrawer";
import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { reserveTypeSchema } from "@/services/api/studies/areas/reserves/schemas";
import type {
  Reserve,
  ReserveType,
  UpdateReserveData,
} from "@/services/api/studies/areas/reserves/types";
import { validateNumber } from "@/utils/validation/number";
import EditIcon from "@mui/icons-material/Edit";
import { useTranslation } from "react-i18next";

interface EditReserveValues {
  type: ReserveType;
  failureCost: number;
  spillageCost: number;
  referenceActivationDuration: number;
  powerActivationRatio: number;
  energyActivationRatio: number;
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
  reserve: Reserve;
  onSubmit: (values: UpdateReserveData) => Promise<void>;
}

const RESERVE_TYPES = reserveTypeSchema.options;

function EditReserveDrawer({ open, onClose, reserve, onSubmit }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<EditReserveValues>) => {
    return onSubmit(dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDrawer
      open={open}
      title={reserve.id}
      titleIcon={EditIcon}
      onCancel={onClose}
      onSubmitSuccessful={onClose}
      config={{ defaultValues: reserve }}
      onSubmit={handleSubmit}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <SelectFE
              label={t("global.type")}
              name="type"
              control={control}
              options={RESERVE_TYPES}
              rules={{ required: t("form.field.required") }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.failureCost")}
              name="failureCost"
              control={control}
              rules={{
                required: t("form.field.required"),
                validate: validateNumber({ min: 0 }),
              }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.spillageCost")}
              name="spillageCost"
              control={control}
              rules={{
                required: t("form.field.required"),
                validate: validateNumber({ min: 0 }),
              }}
            />
          </Fieldset>
          <Fieldset fullFieldWidth legend={t("study.modeling.reserves.field.storageParticipation")}>
            <NumberFE
              label={t("study.modeling.reserves.field.referenceActivationDuration")}
              name="referenceActivationDuration"
              control={control}
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.powerActivationRatio")}
              name="powerActivationRatio"
              control={control}
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.energyActivationRatio")}
              name="energyActivationRatio"
              control={control}
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
          </Fieldset>
        </>
      )}
    </FormDrawer>
  );
}

export default EditReserveDrawer;
