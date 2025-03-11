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

import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useFormContextPlus } from "../../../../../../../common/Form";
import type { AllocationFormFields } from "./utils";
import AllocationField from "./AllocationField";
import DynamicList from "../../../../../../../common/DynamicList";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreasById } from "../../../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../../../types/types";
import { useAreasOptions } from "../hooks/useAreasOptions";

function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areasById = useAppSelector((state) => getAreasById(state, studyId));
  const { control } = useFormContextPlus<AllocationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "allocation",
  });

  const options = useAreasOptions(fields);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DynamicList
      items={fields}
      renderItem={(item, index) => (
        <AllocationField
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
    />
  );
}

export default Fields;
