import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import ThermalView from "./ThermalView";

function Thermal() {
  const fixedGroupList = [
    "Gas",
    "Hard Coal",
    "Lignite",
    "Mixed fuel",
    "Nuclear",
    "Oil",
    "Other",
    "Other 2",
    "Other 3",
    "Other 4",
  ];
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  return (
    <ClusterRoot
      study={study}
      fixedGroupList={fixedGroupList}
      type="thermals"
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ cluster, groupList, nameList }) => (
        <ThermalView
          study={study}
          cluster={cluster}
          groupList={groupList}
          nameList={nameList}
        />
      )}
    </ClusterRoot>
  );
}

export default Thermal;
