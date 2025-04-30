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

import { useEffect, useState } from "react";
import type { Area } from "../../../../../../types/types";
import PropertiesView from "../../../../../common/PropertiesView";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../redux/selectors";
import ListElement from "../../common/ListElement";
import { transformNameToId } from "../../../../../../services/utils";

interface PropsType {
  studyId: string;
  onClick: (name: string) => void;
  currentArea?: string;
}
function AreaPropsView(props: PropsType) {
  const { onClick, currentArea, studyId } = props;
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const [areaNameFilter, setAreaNameFilter] = useState<string>();
  const [filteredAreas, setFilteredAreas] = useState<Area[]>(areas || []);

  useEffect(() => {
    const filter = (): Area[] => {
      if (areas) {
        return areas.filter(
          (s) => !areaNameFilter || s.name.search(new RegExp(areaNameFilter, "i")) !== -1,
        );
      }
      return [];
    };
    setFilteredAreas(
      filter().map((el) => ({
        ...el,
        name: transformNameToId(el.name),
        label: el.name,
      })),
    );
  }, [areas, areaNameFilter]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        <ListElement
          list={filteredAreas}
          currentElement={currentArea}
          setSelectedItem={(elm) => onClick(transformNameToId(elm.name))}
        />
      }
      secondaryContent={<div />}
      onSearchFilterChange={(e) => setAreaNameFilter(e as string)}
    />
  );
}

export default AreaPropsView;
