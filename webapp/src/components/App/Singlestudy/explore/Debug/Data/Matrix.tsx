import { MatrixStats } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import type { DataCompProps } from "../utils";

function Matrix({ studyId, filename, filePath, enableImport }: DataCompProps) {
  return (
    <ViewWrapper>
      <MatrixInput
        title={filename}
        study={studyId}
        url={filePath}
        computStats={MatrixStats.NOCOL}
        disableImport={!enableImport}
      />
    </ViewWrapper>
  );
}

export default Matrix;
