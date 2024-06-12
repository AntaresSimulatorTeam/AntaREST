import { Box } from "@mui/material";
import SplitView, { SplitViewProps } from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

interface Props {
  types: [HydroMatrixType, HydroMatrixType];
  direction?: SplitViewProps["direction"];
  sizes: [number, number];
  form?: React.ComponentType;
}

function SplitHydroMatrix({ types, direction, sizes, form: Form }: Props) {
  return (
    <>
      {Form && (
        <Box sx={{ width: 1, p: 1 }}>
          <Form />
        </Box>
      )}
      <SplitView
        id={`hydro-${types[0]}-${types[1]}`}
        direction={direction}
        sizes={sizes}
      >
        <HydroMatrix type={types[0]} />
        <HydroMatrix type={types[1]} />
      </SplitView>
    </>
  );
}

export default SplitHydroMatrix;
