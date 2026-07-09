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
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useArea from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-hooks/useArea";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type { ReserveGlobalParameters } from "@/services/api/studies/areas/reserves/types";
import SettingsIcon from "@mui/icons-material/Settings";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { validateNumber } from "@/utils/validation/number";

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function EditGlobalParametersDrawer({ open, onClose }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { id: studyId } = useStudy();
  const { id: areaId } = useArea();
  const { queryKey } = reserveQueries.globalParameters(studyId, areaId);

  const updateMutation = useMutation({
    ...reserveMutations.updateGlobalParameters(studyId, areaId),
    onSuccess: (updatedParameters) => {
      queryClient.setQueryData(queryKey, updatedParameters);
    },
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<ReserveGlobalParameters>) => {
    return updateMutation.mutateAsync({ studyId, areaId, data: dirtyValues });
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
              rules={{ validate: validateNumber({ min: 0 }) }}
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
              rules={{ validate: validateNumber({ min: 0 }) }}
            />
          </Fieldset>
        </>
      )}
    </FormDrawer>
  );
}

export default EditGlobalParametersDrawer;
