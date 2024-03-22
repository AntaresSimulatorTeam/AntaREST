import { useEffect, useMemo, useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import PropertiesView from "../../../../../common/PropertiesView";
import ListElement from "../../common/ListElement";
import AddDialog from "./AddDialog";
import { BindingConstraint } from "./BindingConstView/utils";

interface Props {
  studyId: StudyMetadata["id"];
  list: BindingConstraint[];
  onClick: (name: string) => void;
  currentBindingConst?: string;
  reloadConstraintsList: VoidFunction;
}

// TODO rename ConstraintsList
function BindingConstPropsView({
  studyId,
  list,
  onClick,
  currentBindingConst,
  reloadConstraintsList,
}: Props) {
  const [bindingConstNameFilter, setBindingConstNameFilter] =
    useState<string>();
  const [addBindingConst, setAddBindingConst] = useState(false);
  const [filteredBindingConst, setFilteredBindingConst] = useState<
    BindingConstraint[]
  >(list || []);

  useEffect(() => {
    const filter = (): BindingConstraint[] => {
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
          studyId={studyId}
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
