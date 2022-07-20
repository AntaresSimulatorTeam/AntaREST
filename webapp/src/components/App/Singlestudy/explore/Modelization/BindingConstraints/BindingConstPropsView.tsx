import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../common/types";
import PropertiesView from "../../../../../common/PropertiesView";
import ListElement from "../../common/ListElement";
import AddBindingConstDialog from "./AddBindingConstDialog";
import { BindingConstType } from "./BindingConstView/utils";

interface PropsType {
  onClick: (name: string) => void;
  list: Array<BindingConstType>;
  studyId: StudyMetadata["id"];
  currentBindingConst?: string;
}
function BindingConstPropsView(props: PropsType) {
  const { onClick, currentBindingConst, studyId, list } = props;
  const [t] = useTranslation();
  const [bindingConstNameFilter, setBindingConstNameFilter] =
    useState<string>();
  const [addBindingConst, setAddBindingConst] = useState(false);
  const [filteredBindingConst, setFilteredBindingConst] = useState<
    Array<BindingConstType>
  >(list || []);

  useEffect(() => {
    const filter = (): Array<BindingConstType> => {
      if (list) {
        return list.filter(
          (s) =>
            !bindingConstNameFilter ||
            s.name.search(new RegExp(bindingConstNameFilter, "i")) !== -1
        );
      }
      return [];
    };
    setFilteredBindingConst(filter());
  }, [list, bindingConstNameFilter]);

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
        <AddBindingConstDialog
          open={addBindingConst}
          studyId={studyId}
          title={t("study.modelization.bindingConst.newBindingConst")}
          onCancel={() => setAddBindingConst(false)}
        />
      )}
    </>
  );
}

BindingConstPropsView.defaultProps = {
  currentBindingConst: undefined,
};

export default BindingConstPropsView;
