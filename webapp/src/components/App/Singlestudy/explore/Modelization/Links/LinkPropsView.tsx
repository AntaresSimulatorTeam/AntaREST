import { useEffect, useState } from "react";
import PropertiesView from "../../../../../common/PropertiesView";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLinkId, getLinks } from "../../../../../../redux/selectors";
import ListElement from "../../common/ListElement";
import { LinkElement } from "../../../../../../common/types";

interface PropsType {
  studyId: string;
  onClick: (name: string) => void;
}
function LinkPropsView(props: PropsType) {
  const { onClick, studyId } = props;
  const currentLinkId = useAppSelector(getCurrentLinkId);
  const links = useAppSelector((state) => getLinks(state, studyId));
  const [linkNameFilter, setLinkNameFilter] = useState<string>();
  const [filteredLinks, setFilteredLinks] = useState<Array<LinkElement>>(
    links || []
  );

  useEffect(() => {
    const filter = (): Array<LinkElement> => {
      if (links) {
        return links.filter(
          (s) =>
            !linkNameFilter ||
            s.name.search(new RegExp(linkNameFilter, "i")) !== -1
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
