import { MatrixStats } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import type { DataCompProps } from "../utils";

function Matrix({ studyId, filename, filePath, enableImport }: DataCompProps) {
  return (
    <MatrixInput
      title={filename}
      study={studyId}
      url={filePath}
      computStats={MatrixStats.NOCOL}
      disableImport={!enableImport}
    />
  );
}

export default Matrix;
