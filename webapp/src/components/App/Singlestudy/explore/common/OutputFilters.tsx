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

import { useMemo } from "react";
import type { FieldPath } from "react-hook-form";
import { useTranslation } from "react-i18next";
import SelectFE from "../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../common/Fieldset";
import type { ControlPlus } from "../../../../common/Form/types";
import type { FilteringType } from "./types";

interface FilterFieldValues {
  filterSynthesis: FilteringType[];
  filterByYear: FilteringType[];
}

interface Props<T extends FilterFieldValues> {
  onAutoSubmit: (name: keyof FilterFieldValues, selection: string) => void;
  control: ControlPlus<T>;
}

function OutputFilters<T extends FilterFieldValues>(props: Props<T>) {
  const { onAutoSubmit, control } = props;
  const [t] = useTranslation();

  const filterOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly", "monthly", "annual"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t],
  );

  const renderFilter = (filterName: keyof FilterFieldValues) => (
    <SelectFE
      name={filterName as FieldPath<T>}
      multiple
      options={filterOptions}
      label={t(`study.outputFilters.${filterName}`)}
      variant="outlined"
      control={control}
      rules={{
        onAutoSubmit: (value) => {
          const selection = value ? (value as string[]).filter((val) => val !== "") : [];
          onAutoSubmit(filterName, selection.join(", "));
        },
      }}
      sx={{ maxWidth: 220 }}
    />
  );

  return (
    <Fieldset legend={t("study.outputFilters")} sx={{ py: 1 }}>
      {renderFilter("filterSynthesis")}
      {renderFilter("filterByYear")}
    </Fieldset>
  );
}

export default OutputFilters;
