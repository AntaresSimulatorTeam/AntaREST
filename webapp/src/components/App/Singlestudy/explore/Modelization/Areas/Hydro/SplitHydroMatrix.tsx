import SplitView, { SplitViewProps } from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

interface Props {
  types: [HydroMatrixType, HydroMatrixType];
  direction?: SplitViewProps["direction"];
  sizes: [number, number];
}

function SplitHydroMatrix({ types, direction, sizes }: Props) {
  return (
    <SplitView direction={direction} sizes={sizes}>
      <HydroMatrix type={types[0]} />
      <HydroMatrix type={types[1]} />
    </SplitView>
  );
}

export default SplitHydroMatrix;
