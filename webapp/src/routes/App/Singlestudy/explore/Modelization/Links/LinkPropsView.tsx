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
import PropertiesView from "../../../../../common/PropertiesView";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLinkId, getLinks } from "../../../../../../redux/selectors";
import ListElement from "../../common/ListElement";
import type { LinkElement } from "../../../../../../types/types";

interface PropsType {
  studyId: string;
  onClick: (name: string) => void;
}
function LinkPropsView(props: PropsType) {
  const { onClick, studyId } = props;
  const currentLinkId = useAppSelector(getCurrentLinkId);
  const links = useAppSelector((state) => getLinks(state, studyId));
  const [linkNameFilter, setLinkNameFilter] = useState<string>();
  const [filteredLinks, setFilteredLinks] = useState<LinkElement[]>(links || []);

  useEffect(() => {
    const filter = (): LinkElement[] => {
      if (links) {
        return links.filter(
          (s) => !linkNameFilter || s.name.search(new RegExp(linkNameFilter, "i")) !== -1,
        );
      }
      return [];
    };
    setFilteredLinks(filter());
  }, [links, linkNameFilter]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        <ListElement
          list={filteredLinks}
          currentElement={currentLinkId}
          currentElementKeyToTest="id"
          setSelectedItem={(elm) => onClick(elm.id)}
        />
      }
      secondaryContent={<div />}
      onSearchFilterChange={(e) => setLinkNameFilter(e as string)}
    />
  );
}

export default LinkPropsView;
