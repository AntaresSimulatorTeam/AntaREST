import { Box } from "@mui/material";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import FormTable from "../../../../../../../common/FormTable";

const handleSubmit = (data: SubmitHandlerPlus) => {
  console.log("data", data);
};

const data = {
  east: {
    All: true,
    Map1: false,
    Map2: false,
    Map4: true,
    Map5: false,
  },
  north: {
    All: true,
    Map1: false,
    Map2: false,
    Map4: true,
    Map5: true,
  },
  west: {
    All: true,
    Map1: false,
    Map2: true,
    Map4: false,
    Map5: true,
  },
};

function Layers() {
  return (
    <Box>
      <FormTable defaultValues={data} onSubmit={handleSubmit} />
    </Box>
  );
}

export default Layers;
