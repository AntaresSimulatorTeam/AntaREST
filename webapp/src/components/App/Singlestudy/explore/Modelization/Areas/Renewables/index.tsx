import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import { getDefaultValues } from "../common/utils";
import RenewableForm from "./RenewableForm";
import { fixedGroupList, noDataValues } from "./utils";

function Renewables() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  return (
    <ClusterRoot
      study={study}
      fixedGroupList={fixedGroupList}
      type="renewables"
      noDataValues={noDataValues}
      getDefaultValues={getDefaultValues}
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ study, cluster, area, groupList }) => (
        <RenewableForm
          study={study}
          cluster={cluster}
          area={area}
          groupList={groupList}
        />
      )}
    </ClusterRoot>
  );
}

export default Renewables;
