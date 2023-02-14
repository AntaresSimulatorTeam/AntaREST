import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import { transformNameToId } from "../../../../../../../services/utils";
import DocLink from "../../../../../../common/DocLink";
import Form from "../../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { ACTIVE_WINDOWS_DOC_PATH } from "../../BindingConstraints/BindingConstView/utils";
import ClusterRoot from "../common/ClusterRoot";
import { getDefaultValues } from "../common/utils";
import Fields from "./Fields";
import {
  CLUSTER_GROUP_OPTIONS,
  getRenewableFormFields,
  RenewableFormFields,
  updateRenewableFormFields,
} from "./utils";

function Renewables() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit =
    (areaId: string, clusterId: string) =>
    ({ dirtyValues }: SubmitHandlerPlus<RenewableFormFields>) => {
      return updateRenewableFormFields(
        study.id,
        areaId,
        clusterId,
        dirtyValues
      );
    };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ClusterRoot
      study={study}
      fixedGroupList={CLUSTER_GROUP_OPTIONS}
      type="renewables"
      noDataValues={{
        enabled: true,
        unitcount: 0,
        nominalcapacity: 0,
      }}
      getDefaultValues={getDefaultValues}
      backButtonName={t("study.modelization.clusters.backClusterList")}
    >
      {({ study, cluster, area }) => (
        <>
          <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#renewable`} isAbsolute />
          <Form
            key={study.id}
            config={{
              asyncDefaultValues: () => {
                return getRenewableFormFields(study.id, area, cluster);
              },
            }}
            onSubmit={handleSubmit(area, cluster)}
            autoSubmit
          >
            <Fields />
          </Form>
          <Box
            sx={{
              width: 1,
              display: "flex",
              flexDirection: "column",
              height: "500px",
            }}
          >
            <MatrixInput
              study={study}
              url={`input/renewables/series/${area}/${transformNameToId(
                cluster
              )}/series`}
              computStats={MatrixStats.NOCOL}
            />
          </Box>
        </>
      )}
    </ClusterRoot>
  );
}

export default Renewables;
