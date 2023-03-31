import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { t } from "i18next";
import { AxiosError } from "axios";
import Form from "../../../../../../../common/Form";
import Fields from "./Fields";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import {
  AllocationFormFields,
  getAllocationFormFields,
  setAllocationFormFields,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";

function Allocation() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<AllocationFormFields>) => {
    try {
      setAllocationFormFields(studyId, areaId, {
        allocation: data.values.allocation,
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("study.modelization.hydro.allocation.error.field.delete"),
        e as AxiosError
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: 1,
        height: 1,
        p: 1,
        overflowX: "auto",
      }}
    >
      <Form
        key={studyId + areaId}
        config={{
          asyncDefaultValues: () => getAllocationFormFields(studyId, areaId),
        }}
        onSubmit={handleSubmit}
      >
        <Fields />
      </Form>
    </Box>
  );
}

export default Allocation;
