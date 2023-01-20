import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import { Root } from "./style";
import DocLink from "../../../../../common/DocLink";

function MiscGen() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/misc-gen/miscgen-${currentArea}`;
  const colmunsNames = [
    "CHP",
    "Bio Mass",
    "Bio Gaz",
    "Waste",
    "GeoThermal",
    "Other",
    "PSP",
    "ROW Balance",
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <DocLink to="misc-gen" isAbsolute />
      <MatrixInput
        study={study}
        url={url}
        columnsNames={colmunsNames}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default MiscGen;
