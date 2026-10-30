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
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  RENEWABLE_GROUPS,
  TS_INTERPRETATION_OPTIONS,
} from "@/services/api/studies/areas/renewables/constants";
import type { RenewableCluster } from "@/services/api/studies/areas/renewables/types";
import { buildKey } from "@/utils/reactUtils";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useUpdateRenewableCluster from "../-hooks/useUpdateRenewableCluster";
import useRenewableCluster from "./-hooks/useRenewableCluster";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId/parameters",
)({
  component: Parameters,
});

function Parameters() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const study = useStudy();
  const { data: renewableCluster } = useRenewableCluster(params);
  const updateRenewableCluster = useUpdateRenewableCluster(params);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<RenewableCluster>) => {
    return updateRenewableCluster.mutateAsync({ values: dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={buildKey(params)}
      config={{ defaultValues: renewableCluster }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control }) => (
        <Fieldset legend={t("study.modeling.clusters.operatingParameters")}>
          <SwitchFE label={t("study.modeling.clusters.enabled")} name="enabled" control={control} />
          {semver.lt(study.version, "9.3.0") ? (
            <SelectFE
              label={t("global.group")}
              name="group"
              control={control}
              options={RENEWABLE_GROUPS}
              startCaseLabel={false}
              sx={{
                alignSelf: "center",
              }}
            />
          ) : (
            <StringFE
              label={t("global.group")}
              name="group"
              datalist={RENEWABLE_GROUPS}
              control={control}
            />
          )}
          <SelectFE
            label={t("study.modeling.clusters.tsInterpretation")}
            name="tsInterpretation"
            control={control}
            options={TS_INTERPRETATION_OPTIONS}
            sx={{
              alignSelf: "center",
            }}
          />
          <NumberFE
            label={t("study.modeling.clusters.unitcount")}
            name="unitCount"
            control={control}
            rules={{
              min: {
                value: 1,
                message: t("form.field.minValue", { 0: 1 }),
              },
              setValueAs: Math.floor,
            }}
          />
          <NumberFE
            label={t("study.modeling.clusters.nominalCapacity")}
            name="nominalCapacity"
            control={control}
            rules={{
              min: {
                value: 0,
                message: t("form.field.minValue", { 0: 0 }),
              },
            }}
          />
        </Fieldset>
      )}
    </Form>
  );
}
