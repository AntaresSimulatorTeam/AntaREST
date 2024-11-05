/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { useOutletContext } from "react-router-dom";

import { StudyMetadata, UpdateAreaUi } from "@/common/types";
import PropertiesView from "@/components/common/PropertiesView";
import { StudyMapNode } from "@/redux/ducks/studyMaps";
import { setCurrentArea } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentLink, getCurrentStudyMapNode } from "@/redux/selectors";
import { isSearchMatching } from "@/utils/stringUtils";

import ListElement from "../../../common/ListElement";

import AreaConfig from "./AreaConfig";
import { AreasContainer } from "./style";

interface Props {
  onAdd: () => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  nodes: StudyMapNode[];
}

function Areas({ onAdd, updateUI, nodes }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [filteredNodes, setFilteredNodes] = useState<StudyMapNode[]>([]);
  const [searchValue, setSearchValue] = useState("");
  const [showAreaConfig, setShowAreaConfig] = useState(false);
  const currentArea = useAppSelector(getCurrentStudyMapNode);
  const currentLink = useAppSelector((state) =>
    getCurrentLink(state, study.id),
  );

  useEffect(() => {
    setFilteredNodes(
      nodes.filter(({ id }) => isSearchMatching(searchValue, id)),
    );
  }, [nodes, searchValue]);

  useEffect(() => {
    setShowAreaConfig(!!(currentArea || currentLink));
  }, [currentArea, currentLink]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <PropertiesView
      mainContent={
        showAreaConfig && (
          <AreasContainer>
            <AreaConfig
              currentArea={currentArea}
              updateUI={updateUI}
              currentLink={currentLink}
            />
          </AreasContainer>
        )
      }
      secondaryContent={
        (!showAreaConfig || (!currentArea && !currentLink)) &&
        filteredNodes.length > 0 && (
          <ListElement
            setSelectedItem={({ id }) => {
              dispatch(setCurrentArea(id));
              setShowAreaConfig(true);
            }}
            list={filteredNodes}
          />
        )
      }
      onSearchFilterChange={(searchValue) => {
        setSearchValue(searchValue);
      }}
      onAdd={onAdd}
    />
  );
}

export default Areas;
