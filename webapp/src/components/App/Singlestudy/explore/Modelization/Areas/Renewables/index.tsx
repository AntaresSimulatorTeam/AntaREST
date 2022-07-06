import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import RenewableView from "./RenewableView";

function Renewables() {
  const fixedGroupList = [
    "Wind Onshore",
    "Wind Offshore",
    "Solar Thermal",
    "Solar PV",
    "Solar Rooftop",
    "Other RES 1",
    "Other RES 2",
    "Other RES 3",
    "Other RES 4",
  ];
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  return (
    <ClusterRoot
      study={study}
      fixedGroupList={fixedGroupList}
      type="renewables"
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ cluster, groupList, nameList }) => (
        <RenewableView
          cluster={cluster}
          groupList={groupList}
          nameList={nameList}
          study={study}
        />
      )}
    </ClusterRoot>
  );
}

export default Renewables;
