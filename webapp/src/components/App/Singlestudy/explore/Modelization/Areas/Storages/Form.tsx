import { useCallback } from "react";
import { Box, Button } from "@mui/material";
import { useParams, useOutletContext, useNavigate } from "react-router-dom";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import * as RA from "ramda-adjunct";
import { StudyMetadata } from "../../../../../../../common/types";
import Form from "../../../../../../common/Form";
import Fields from "./Fields";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import { Storage, getStorage, updateStorage } from "./utils";
import Matrix from "./Matrix";
import useNavigateOnCondition from "../../../../../../../hooks/useNavigateOnCondition";
import { nameToId } from "../../../../../../../services/utils";

function StorageForm() {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const areaId = useAppSelector(getCurrentAreaId);
  const { storageId = "" } = useParams();

  useNavigateOnCondition({
    deps: [areaId],
    to: `../storages`,
  });

  // prevent re-fetch while useNavigateOnCondition event occurs
  const defaultValues = useCallback(
    async () => {
      const storage = await getStorage(study.id, areaId, storageId);
      return {
        ...storage,
        // Convert to percentage ([0-1] -> [0-100])
        efficiency: storage.efficiency * 100,
        initialLevel: storage.initialLevel * 100,
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<Storage>) => {
    const newValues = { ...dirtyValues };
    // Convert to ratio ([0-100] -> [0-1])
    if (RA.isNumber(newValues.efficiency)) {
      newValues.efficiency /= 100;
    }
    if (RA.isNumber(newValues.initialLevel)) {
      newValues.initialLevel /= 100;
    }
    return updateStorage(study.id, areaId, storageId, newValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: 1, p: 1, overflow: "auto" }}>
      <Button
        color="secondary"
        size="small"
        onClick={() => navigate("../storages")}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start", px: 0 }}
      >
        {t("button.back")}
      </Button>
      <Form
        key={study.id + areaId}
        config={{
          defaultValues,
        }}
        onSubmit={handleSubmit}
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
          <Matrix
            study={study}
            areaId={areaId}
            storageId={nameToId(storageId)}
          />
        </Box>
      </Form>
    </Box>
  );
}

export default StorageForm;
