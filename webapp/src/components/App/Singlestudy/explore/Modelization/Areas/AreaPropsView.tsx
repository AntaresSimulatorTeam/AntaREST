import { useEffect, useState } from "react";
import { Area } from "../../../../../../common/types";
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
  const [filteredAreas, setFilteredAreas] = useState<Array<Area>>(areas || []);

  useEffect(() => {
    const filter = (): Array<Area> => {
      if (areas) {
        return areas.filter(
          (s) =>
            !areaNameFilter ||
            s.name.search(new RegExp(areaNameFilter, "i")) !== -1
        );
      }
      return [];
    };
    setFilteredAreas(
      filter().map((el) => ({
        ...el,
        name: transformNameToId(el.name),
        label: el.name,
      }))
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

AreaPropsView.defaultProps = {
  currentArea: undefined,
};

export default AreaPropsView;
