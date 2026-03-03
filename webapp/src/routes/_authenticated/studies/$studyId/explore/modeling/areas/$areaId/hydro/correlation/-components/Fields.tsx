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

import DynamicList from "@/components/DynamicList";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { useFieldArray, useFormContext } from "react-hook-form";
import type { CorrelationFormFields } from "../-utils";
import { useAreasOptions } from "../../-hooks/useAreasOptions";
import useArea from "../../../-hooks/useArea";
import useAppSelector from "../../../../../../../../../../../redux/hooks/useAppSelector";
import { getAreasById } from "../../../../../../../../../../../redux/selectors";
import CorrelationField from "./CorrelationField";

function Fields() {
  const study = useStudy();
  const area = useArea();
  const areasById = useAppSelector((state) => getAreasById(state, study.id));

  const { control } = useFormContext<CorrelationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "correlation",
  });

  const options = useAreasOptions(fields);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DynamicList
      items={fields}
      renderItem={(item, index) => (
        <CorrelationField
          key={item.id}
          field={item}
          index={index}
          label={areasById?.[item.areaId]?.name}
        />
      )}
      options={options}
      onAdd={(value) =>
        append({
          areaId: value,
          coefficient: 0,
        })
      }
      onDelete={remove}
      allowEmpty={false}
      disableDelete={(item) => item.areaId === area.id}
    />
  );
}

export default Fields;
