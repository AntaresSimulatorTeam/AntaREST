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

import { useEffect, useMemo, useState } from "react";

import AddDialog from "./AddDialog";
import { BindingConstraint } from "./BindingConstView/utils";
import PropertiesView from "@/components/common/PropertiesView";
import ListElement from "../../common/ListElement";

interface Props {
  list: BindingConstraint[];
  onClick: (name: string) => void;
  currentConstraint?: string;
  reloadConstraintsList: VoidFunction;
}

// TODO rename ConstraintsList
function BindingConstPropsView({
  list,
  onClick,
  currentConstraint,
  reloadConstraintsList,
}: Props) {
  const [searchedConstraint, setSearchedConstraint] = useState("");
  const [addBindingConst, setAddBindingConst] = useState(false);
  const [filteredConstraints, setFilteredConstraints] = useState(list);

  useEffect(() => {
    if (!list) {
      setFilteredConstraints([]);
      return;
    }

    if (!searchedConstraint) {
      setFilteredConstraints(list);
      return;
    }

    const pattern = new RegExp(searchedConstraint, "i");
    const filtered = list.filter((s) => pattern.test(s.name));

    setFilteredConstraints(filtered);
  }, [list, searchedConstraint]);

  const existingConstraints = useMemo(
    () => list.map(({ name }) => name),
    [list],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <PropertiesView
        mainContent={
          <ListElement
            list={filteredConstraints.map((constraint) => ({
              label: constraint.name,
              name: constraint.id,
            }))}
            currentElement={currentConstraint}
            setSelectedItem={(elm) => onClick(elm.name)}
          />
        }
        secondaryContent={<div />}
        onAdd={() => setAddBindingConst(true)}
        onSearchFilterChange={(e) => setSearchedConstraint(e)}
      />
      {addBindingConst && (
        <AddDialog
          open={addBindingConst}
          existingConstraints={existingConstraints}
          reloadConstraintsList={reloadConstraintsList}
          onClose={() => setAddBindingConst(false)}
        />
      )}
    </>
  );
}

export default BindingConstPropsView;
