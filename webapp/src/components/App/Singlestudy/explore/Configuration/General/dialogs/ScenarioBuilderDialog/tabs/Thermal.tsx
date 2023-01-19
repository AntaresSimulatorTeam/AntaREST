import { useContext, useEffect, useMemo, useState } from "react";
import useStudySynthesis from "../../../../../../../../../redux/hooks/useStudySynthesis";
import { getAreas } from "../../../../../../../../../redux/selectors";
import { isSearchMatching } from "../../../../../../../../../utils/textUtils";
import PropertiesView from "../../../../../../../../common/PropertiesView";
import SplitLayoutView from "../../../../../../../../common/SplitLayoutView";
import UsePromiseCond from "../../../../../../../../common/utils/UsePromiseCond";
import ListElement from "../../../../../common/ListElement";
import ConfigContext from "../ConfigContext";
import Table from "./Table";

interface Props {
  nbYears: number;
}

function Thermal(props: Props) {
  const { nbYears } = props;
  const { studyId } = useContext(ConfigContext);
  const res = useStudySynthesis({ studyId, selector: getAreas });
  const [selectedAreaId, setSelectedAreaId] = useState("");
  const [searchValue, setSearchValue] = useState("");

  const filteredAreas = useMemo(
    () =>
      res.data?.filter(({ name }) => isSearchMatching(searchValue, name)) || [],
    [res.data, searchValue]
  );

  useEffect(() => {
    setSelectedAreaId(filteredAreas.length > 0 ? filteredAreas[0].id : "");
  }, [filteredAreas]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={() => (
        <SplitLayoutView
          sx={{
            height: 1,
            ".SplitLayoutView__Left": { pl: 0 },
          }}
          left={
            <PropertiesView
              sx={{ ".SearchFE": { m: 0, pb: 2 } }}
              mainContent={
                <ListElement
                  sx={{ p: 0 }}
                  list={filteredAreas}
                  currentElement={selectedAreaId}
                  currentElementKeyToTest="id"
                  setSelectedItem={({ id }) => setSelectedAreaId(id)}
                />
              }
              onSearchFilterChange={setSearchValue}
            />
          }
          right={
            <Table
              nbYears={nbYears}
              symbol="t"
              rowType="thermal"
              areaId={selectedAreaId}
            />
          }
        />
      )}
    />
  );
}

export default Thermal;
