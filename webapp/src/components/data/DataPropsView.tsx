import { useState } from "react";
import { MatrixDataSetDTO, MatrixInfoDTO } from "../../common/types";
import PropertiesView from "../common/PropertiesView";
import DataListing from "./DataListing";
import { StyledListingBox } from "./styles";

interface PropTypes {
  dataset: Array<MatrixDataSetDTO>;
  selectedItem: string;
  setSelectedItem: (item: string) => void;
  onAdd: () => void;
}

function DataPropsView(props: PropTypes) {
  const { dataset, selectedItem, setSelectedItem, onAdd } = props;
  const [filteredDatas, setFilteredDatas] = useState<Array<MatrixDataSetDTO>>();

  const filter = (input: string): Array<MatrixDataSetDTO> => {
    return dataset.filter(
      (item) =>
        item.name.search(input) >= 0 ||
        !!item.matrices.find(
          (matrix: MatrixInfoDTO) => matrix.id.search(input) >= 0
        )
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
              datasets={dataset}
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
