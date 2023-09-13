import { Box, Button } from "@mui/material";
import { useParams, useOutletContext, useNavigate } from "react-router-dom";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import { nameToId } from "../../../../../../../services/utils";
import Form from "../../../../../../common/Form";
import Fields from "./Fields";
import Matrix from "./Matrix";
import {
  ThermalCluster,
  getThermalCluster,
  updateThermalCluster,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";

function ThermalForm() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { clusterId = "" } = useParams();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit =
    (areaId: string, clusterId: string) =>
    ({ dirtyValues }: SubmitHandlerPlus<ThermalCluster>) => {
      return updateThermalCluster(study.id, areaId, clusterId, dirtyValues);
    };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: 1, p: 1, overflow: "auto" }}>
      <Button
        color="secondary"
        size="small"
        onClick={() => navigate(-1)}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start", px: 0 }}
      >
        {t("button.back")}
      </Button>
      <Form
        key={study.id + areaId}
        config={{
          defaultValues: () => {
            return getThermalCluster(study.id, areaId, clusterId);
          },
        }}
        onSubmit={handleSubmit(areaId, clusterId)}
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
          <Matrix study={study} area={areaId} cluster={nameToId(clusterId)} />
        </Box>
      </Form>
    </Box>
  );
}

export default ThermalForm;
