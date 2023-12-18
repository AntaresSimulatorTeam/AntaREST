import { useEffect, useMemo, useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import PropertiesView from "../../../../../common/PropertiesView";
import ListElement from "../../common/ListElement";
import AddDialog from "./AddDialog";
import { BindingConstFields } from "./BindingConstView/utils";

interface Props {
  onClick: (name: string) => void;
  list: Array<BindingConstFields>;
  studyId: StudyMetadata["id"];
  currentBindingConst?: string;
}

function BindingConstPropsView(props: Props) {
  const { onClick, currentBindingConst, studyId, list } = props;
  const [bindingConstNameFilter, setBindingConstNameFilter] =
    useState<string>();
  const [addBindingConst, setAddBindingConst] = useState(false);
  const [filteredBindingConst, setFilteredBindingConst] = useState<
    Array<BindingConstFields>
  >(list || []);

  useEffect(() => {
    const filter = (): Array<BindingConstFields> => {
      if (list) {
        return list.filter(
          (s) =>
            !bindingConstNameFilter ||
            s.name.search(new RegExp(bindingConstNameFilter, "i")) !== -1,
        );
      }
      return [];
    };
    setFilteredBindingConst(filter());
  }, [list, bindingConstNameFilter]);

  const existingConstraints = useMemo(
    () => list.map(({ name }) => name.toLowerCase()),
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
            list={filteredBindingConst.map((item) => ({
              label: item.name,
              name: item.id,
            }))}
            currentElement={currentBindingConst}
            setSelectedItem={(elm) => onClick(elm.name)}
          />
        }
        secondaryContent={<div />}
        onAdd={() => setAddBindingConst(true)}
        onSearchFilterChange={(e) => setBindingConstNameFilter(e as string)}
      />
      {addBindingConst && (
        <AddDialog
          open={addBindingConst}
          studyId={studyId}
          existingConstraints={existingConstraints}
          onClose={() => setAddBindingConst(false)}
        />
      )}
    </>
  );
}

BindingConstPropsView.defaultProps = {
  currentBindingConst: undefined,
};

export default BindingConstPropsView;
