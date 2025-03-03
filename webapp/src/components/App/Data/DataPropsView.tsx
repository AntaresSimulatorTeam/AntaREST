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

import { useState } from "react";
import type { MatrixDataSetDTO, MatrixInfoDTO } from "../../../types/types";
import PropertiesView from "../../common/PropertiesView";
import DataListing from "./DataListing";
import { StyledListingBox } from "./styles";

interface PropTypes {
  dataset: MatrixDataSetDTO[];
  selectedItem: string;
  setSelectedItem: (item: string) => void;
  onAdd?: () => void;
}

function DataPropsView(props: PropTypes) {
  const { dataset, selectedItem, setSelectedItem, onAdd } = props;
  const [filteredDatas, setFilteredDatas] = useState<MatrixDataSetDTO[]>();

  const filter = (input: string): MatrixDataSetDTO[] => {
    return dataset.filter(
      (item) =>
        item.name.search(input) >= 0 ||
        !!item.matrices.find((matrix: MatrixInfoDTO) => matrix.id.search(input) >= 0),
    );
  };

  const onChange = async (currentName: string) => {
    if (currentName !== "") {
      const f = filter(currentName);
      setFilteredDatas(f);
    } else {
      setFilteredDatas(undefined);
    }
  };

  return (
    <PropertiesView
      mainContent={
        !filteredDatas && (
          <StyledListingBox>
            <DataListing
              datasets={dataset}
              selectedItem={selectedItem}
              setSelectedItem={setSelectedItem}
            />
          </StyledListingBox>
        )
      }
      secondaryContent={
        filteredDatas && (
          <StyledListingBox>
            <DataListing
              datasets={filteredDatas}
              selectedItem={selectedItem}
              setSelectedItem={setSelectedItem}
            />
          </StyledListingBox>
        )
      }
      onSearchFilterChange={(e) => onChange(e as string)}
      onAdd={onAdd}
    />
  );
}

export default DataPropsView;
