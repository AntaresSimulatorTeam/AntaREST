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

import SelectFE from "@/components/fieldEditors/SelectFE";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import { useFormContextPlus } from "@/hooks/useFormContextPlus";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "@/redux/selectors";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { isBindingConstraintClusterTerm } from "@/services/api/studies/bindingConstraints/utils";
import { useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import TermDataFieldSkeleton from "./TermDataFieldSkeleton";

function ClusterTermDataFE({ index }: { index: number }) {
  const study = useStudy();
  const { t } = useTranslation();
  const { control, setValue } = useFormContextPlus<BindingConstraint>();
  const currentArea = useWatch({ control, name: `terms.${index}.data.area` });
  const currentCluster = useWatch({ control, name: `terms.${index}.data.cluster` });

  const clusterTermsData = useWatch({
    control,
    name: "terms",
    compute: (terms) => {
      return terms.filter(isBindingConstraintClusterTerm).map((term) => term.data);
    },
  });

  // TODO: optimize by using Tanstack Query
  const response = useStudySynthesis({
    studyId: study.id,
    selector: (state) => {
      const linkAndClusters = getLinksAndClusters(state, study.id);

      const areaOptions = linkAndClusters.clusters.map(({ element }) => ({
        label: element.name,
        value: element.id,
      }));

      const clusterList =
        linkAndClusters.clusters.find(({ element }) => element.id === currentArea)?.item_list || [];

      const clusterOptions = clusterList
        .filter(({ id }) => id === currentCluster || !isClusterTermExist(currentArea, id))
        .map(({ name, id }) => ({
          label: name,
          value: id,
        }));

      return [areaOptions, clusterOptions];
    },
  });

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  function isClusterTermExist(area: string, cluster: string) {
    return clusterTermsData.some(
      (termData) => termData.area === area && termData.cluster === cluster,
    );
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaChange = () => {
    setValue(`terms.${index}.data.cluster`, "");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={response}
      keepLastResolvedOnReload
      ifPending={() => <TermDataFieldSkeleton />}
      ifFulfilled={([areaOptions, clusterOptions]) => (
        <>
          <SelectFE
            label={t("study.area")}
            control={control}
            name={`terms.${index}.data.area`}
            options={areaOptions}
            onChange={handleAreaChange}
            size="extra-small"
            sx={{ minWidth: 150 }}
          />
          <SelectFE
            label={t("study.cluster")}
            control={control}
            name={`terms.${index}.data.cluster`}
            options={clusterOptions}
            size="extra-small"
            sx={{ minWidth: 150 }}
          />
        </>
      )}
    />
  );
}

export default ClusterTermDataFE;
