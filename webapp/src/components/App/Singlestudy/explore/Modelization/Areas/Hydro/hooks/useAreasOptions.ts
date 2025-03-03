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
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../../../types/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../../../redux/selectors";
import type { DynamicListProps } from "../../../../../../../common/DynamicList";
import type { AreaCoefficientItem } from "../utils";

export function useAreasOptions(fields: AreaCoefficientItem[]): DynamicListProps["options"] {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();

  const areas = useAppSelector((state) => getAreas(state, studyId));

  const options = useMemo(() => {
    const areaIds = fields.map((field) => field.areaId);
    return areas
      .filter((area) => !areaIds.includes(area.id))
      .map((area) => ({
        label: area.name,
        value: area.id,
      }));
  }, [areas, fields]);

  return options;
}
