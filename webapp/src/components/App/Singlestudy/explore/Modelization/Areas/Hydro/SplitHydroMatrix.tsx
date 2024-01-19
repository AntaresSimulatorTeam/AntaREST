import SplitView, { SplitViewProps } from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

interface Props {
  type: HydroMatrixType;
  direction?: SplitViewProps["direction"];
  partnerType: HydroMatrixType;
  splitSizes: SplitViewProps["sizes"];
}

function SplitHydroMatrix({ type, direction, partnerType, splitSizes }: Props) {
  return (
    <SplitView direction={direction} sizes={splitSizes}>
      <HydroMatrix type={type} />
      <HydroMatrix type={partnerType} />
    </SplitView>
  );
}

export default SplitHydroMatrix;
