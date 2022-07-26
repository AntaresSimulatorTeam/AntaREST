import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import ThermalForm from "./ThermalForm";
import { fixedGroupList, getDefaultValues } from "./utils";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  return (
    <ClusterRoot
      study={study}
      fixedGroupList={fixedGroupList}
      type="thermals"
      getDefaultValues={getDefaultValues}
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ study, cluster, area, groupList }) => (
        <ThermalForm
          study={study}
          cluster={cluster}
          area={area}
          groupList={groupList}
        />
      )}
    </ClusterRoot>
  );
}

export default Thermal;
