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

import type { DynamicListProps } from "@/components/DynamicList";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { useMemo } from "react";
import type { AreaCoefficientItem } from "../-utils";
import useAppSelector from "../../../../../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../../../../../redux/selectors";

export function useAreasOptions(fields: AreaCoefficientItem[]): DynamicListProps["options"] {
  const study = useStudy();
  const areas = useAppSelector((state) => getAreas(state, study.id));

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
