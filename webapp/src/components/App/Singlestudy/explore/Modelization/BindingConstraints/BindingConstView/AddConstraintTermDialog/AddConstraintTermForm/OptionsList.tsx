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

import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useFormContext } from "react-hook-form";
import SelectFE from "../../../../../../../../common/fieldEditors/SelectFE";
import type { AllClustersAndLinks } from "../../../../../../../../../types/types";
import { isTermExist, generateTermId, type ConstraintTerm } from "../../utils";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  constraintTerms: ConstraintTerm[];
}

export default function OptionsList({ list, isLink, constraintTerms }: Props) {
  const [t] = useTranslation();

  const { control, setValue, watch, getValues } = useFormContext<ConstraintTerm>();

  // Determines the correct set of options based on whether the term is a link or a cluster.
  const options = isLink ? list.links : list.clusters;

  const areaOptions = options.map(({ element }) => ({
    label: element.name,
    value: element.id,
  }));

  // Watching changes to the primary selection to update secondary options accordingly.
  const primarySelection = watch(isLink ? "data.area1" : "data.area");

  useEffect(() => {
    setValue(isLink ? "data.area2" : "data.cluster", "");
  }, [primarySelection, isLink, setValue]);

  const getAreaOrClusterOptions = () => {
    const selectedArea = getValues(isLink ? "data.area1" : "data.area");

    const foundOption = options.find((option) => option.element.id === selectedArea);

    if (!foundOption) {
      return [];
    }

    return foundOption.item_list
      .filter(
        ({ id }) =>
          !isTermExist(
            constraintTerms,
            generateTermId(
              isLink ? { area1: selectedArea, area2: id } : { area: selectedArea, cluster: id },
            ),
          ),
      )
      .map(({ name, id }) => ({
        label: name,
        value: id,
      }));
  };

  const areaOrClusterOptions = getAreaOrClusterOptions();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SelectFE
        variant="outlined"
        name={isLink ? "data.area1" : "data.area"}
        label={t(`study.${isLink ? "area1" : "area"}`)}
        options={areaOptions}
        control={control}
        sx={{ width: 250 }}
        rules={{ required: true }}
      />
      <SelectFE
        variant="outlined"
        name={isLink ? "data.area2" : "data.cluster"}
        label={t(`study.${isLink ? "area2" : "cluster"}`)}
        options={areaOrClusterOptions}
        control={control}
        sx={{ width: 250, ml: 1, mr: 3 }}
        rules={{ required: true }}
      />
    </>
  );
}
