import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../common/types";
import MatrixInput from "../../../../common/MatrixInput";

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

  return <MatrixInput study={study} url={url} columnsNames={colmunsNames} />;
}

export default MiscGen;
