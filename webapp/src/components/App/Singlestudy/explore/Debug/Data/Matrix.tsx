import { MatrixStats } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import ViewWrapper from "../../../../../common/page/ViewWrapper";

interface Props {
  studyId: string;
  path: string;
}

function Matrix({ studyId, path }: Props) {
  const filename = path.split("/").pop();
  const isUserFolder = path.startsWith("/user/");

  return (
    <ViewWrapper>
      <MatrixInput
        title={filename}
        study={studyId}
        url={path}
        computStats={MatrixStats.NOCOL}
        disableImport={!isUserFolder}
      />
    </ViewWrapper>
  );
}

export default Matrix;
