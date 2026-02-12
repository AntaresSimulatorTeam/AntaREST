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
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "@/redux/selectors";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { isBindingConstraintLinkTerm } from "@/services/api/studies/bindingConstraints/utils";
import { useFormContext, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import TermDataFieldSkeleton from "./TermDataFieldSkeleton";

function LinkTermDataFE({ index }: { index: number }) {
  const study = useStudy();
  const { t } = useTranslation();
  const { control, setValue } = useFormContext<BindingConstraint>();
  const currentArea1 = useWatch({ control, name: `terms.${index}.data.area1` });
  const currentArea2 = useWatch({ control, name: `terms.${index}.data.area2` });

  const linkTermsData = useWatch({
    control,
    name: "terms",
    compute: (terms) => {
      return terms.filter(isBindingConstraintLinkTerm).map((term) => term.data);
    },
  });

  // TODO: optimize by using Tanstack Query
  const response = useStudySynthesis({
    studyId: study.id,
    selector: (state) => {
      const linkAndClusters = getLinksAndClusters(state, study.id);

      const area1Options = linkAndClusters.links.map(({ element }) => ({
        label: element.name,
        value: element.id,
      }));

      const area2List =
        linkAndClusters.links.find(({ element }) => element.id === currentArea1)?.item_list || [];

      const area2Options = area2List
        .filter(({ id }) => id === currentArea2 || !isLinkTermExist(currentArea1, id))
        .map(({ name, id }) => ({
          label: name,
          value: id,
        }));

      return [area1Options, area2Options];
    },
  });

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  function isLinkTermExist(area1: string, area2: string) {
    return linkTermsData.some((termData) => termData.area1 === area1 && termData.area2 === area2);
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleArea1Change = () => {
    setValue(`terms.${index}.data.area2`, "");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={response}
      keepLastResolvedOnReload
      ifPending={() => <TermDataFieldSkeleton />}
      ifFulfilled={([area1Options, area2Options]) => (
        <>
          <SelectFE
            label={t("study.area1")}
            control={control}
            name={`terms.${index}.data.area1`}
            options={area1Options}
            onChange={handleArea1Change}
            size="extra-small"
            sx={{ minWidth: 150 }}
          />
          <SelectFE
            label={t("study.area2")}
            control={control}
            name={`terms.${index}.data.area2`}
            options={area2Options}
            size="extra-small"
            sx={{ minWidth: 150 }}
          />
        </>
      )}
    />
  );
}

export default LinkTermDataFE;
