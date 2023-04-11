import { Box, Paper } from "@mui/material";
import { useOutletContext } from "react-router";
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

function Allocation() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<AllocationFormFields>) => {
    return setAllocationFormFields(studyId, areaId, {
      allocation: data.values.allocation,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: 1,
        height: 1,
        p: 2,
        overflow: "auto",
      }}
    >
      <Paper
        sx={{
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
        <Form
          key={studyId + areaId}
          config={{
            defaultValues: () => getAllocationFormFields(studyId, areaId),
          }}
          onSubmit={handleSubmit}
          sx={{ p: 3 }}
        >
          <Fields />
        </Form>
      </Paper>
    </Box>
  );
}

export default Allocation;
