import { Box } from "@mui/material";
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
    setAllocationFormFields(studyId, areaId, {
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
        py: 1,
      }}
    >
      <Form
        key={studyId + areaId}
        config={{
          asyncDefaultValues: () => getAllocationFormFields(studyId, areaId),
        }}
        onSubmit={handleSubmit}
        autoSubmit
      >
        <Fields />
      </Form>
    </Box>
  );
}

export default Allocation;
