import { useEffect, useState } from "react";
import PropertiesView from "../../../../../common/PropertiesView";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getStudyLinks } from "../../../../../../redux/selectors";
import ListElement from "../../common/ListElement";
import { LinkElement } from "../../../../../../common/types";

interface PropsType {
  studyId: string;
  onClick: (name: string) => void;
  currentLink?: string;
}
function LinkPropsView(props: PropsType) {
  const { onClick, currentLink, studyId } = props;
  const links = useAppSelector((state) => getStudyLinks(state, studyId));
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
          currentElement={currentLink}
          setSelectedItem={(elm) => onClick(elm.name)}
        />
      }
      secondaryContent={<div />}
      onSearchFilterChange={(e) => setLinkNameFilter(e as string)}
    />
  );
}

LinkPropsView.defaultProps = {
  currentLink: undefined,
};

export default LinkPropsView;
