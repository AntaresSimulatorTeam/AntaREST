import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import { transformNameToId } from "../../../../../../../services/utils";
import Form from "../../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import ClusterRoot from "../common/ClusterRoot";
import { getDefaultValues } from "../common/utils";
import Fields from "./Fields";
import ThermalMatrixView from "./ThermalMatrixView";
import {
  CLUSTER_GROUP_OPTIONS,
  getThermalFormFields,
  noDataValues,
  ThermalFormFields,
  updateThermalFormFields,
} from "./utils";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit =
    (areaId: string, clusterId: string) =>
    ({ dirtyValues }: SubmitHandlerPlus<ThermalFormFields>) => {
      return updateThermalFormFields(study.id, areaId, clusterId, dirtyValues);
    };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ClusterRoot
      study={study}
      fixedGroupList={CLUSTER_GROUP_OPTIONS}
      type="thermals"
      noDataValues={noDataValues}
      getDefaultValues={getDefaultValues}
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ study, cluster, area }) => (
        <Form
          key={study.id + cluster + area}
          config={{
            asyncDefaultValues: () => {
              return getThermalFormFields(study.id, area, cluster);
            },
          }}
          onSubmit={handleSubmit(area, cluster)}
          autoSubmit
        >
          <Fields />
          <Box
            sx={{
              width: 1,
              display: "flex",
              flexDirection: "column",
              height: "500px",
            }}
          >
            <ThermalMatrixView
              study={study}
              area={area}
              cluster={transformNameToId(cluster)}
            />
          </Box>
        </Form>
      )}
    </ClusterRoot>
  );
}

export default Thermal;
