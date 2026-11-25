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
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import FormDrawer from "@/components/FormDrawer";
import { reserveQueries } from "@/queries/reserves/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import useArea from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-hooks/useArea";
import type { ReserveGlobalParameters } from "@/services/api/studies/areas/reserves/types";
import { validateNumber } from "@/utils/validation/number";
import SettingsIcon from "@mui/icons-material/Settings";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import useUpdateReserveGlobalParameters from "../-hooks/useUpdateReserveGlobalParameters";

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function UpdateGlobalParametersDrawer({ open, onClose }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { id: studyId } = useStudy();
  const { id: areaId } = useArea();
  const updateGlobalParameters = useUpdateReserveGlobalParameters({ studyId, areaId });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<ReserveGlobalParameters>) => {
    return updateGlobalParameters.mutateAsync({ data: dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDrawer
      open={open}
      title={t("study.modeling.reserves.globalParameters")}
      titleIcon={SettingsIcon}
      onCancel={onClose}
      onSubmitSuccessful={onClose}
      config={{
        defaultValues: () =>
          queryClient.fetchQuery(reserveQueries.globalParameters(studyId, areaId)),
      }}
      onSubmit={handleSubmit}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth legend={t("study.modeling.reserves.field.up")}>
            <NumberFE
              label={t("study.modeling.reserves.field.referenceActivationDuration")}
              name="referenceActivationDurationUp"
              control={control}
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.energyActivationRatio")}
              name="energyActivationRatioUp"
              control={control}
              rules={{ validate: validateNumber({ min: 0, max: 1 }) }}
            />
          </Fieldset>
          <Fieldset fullFieldWidth legend={t("study.modeling.reserves.field.down")}>
            <NumberFE
              label={t("study.modeling.reserves.field.referenceActivationDuration")}
              name="referenceActivationDurationDown"
              control={control}
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
            <NumberFE
              label={t("study.modeling.reserves.field.energyActivationRatio")}
              name="energyActivationRatioDown"
              control={control}
              rules={{ validate: validateNumber({ min: 0, max: 1 }) }}
            />
          </Fieldset>
        </>
      )}
    </FormDrawer>
  );
}

export default UpdateGlobalParametersDrawer;
