import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import { Root, Content } from "./style";
import MatrixInput from "../../../../../common/MatrixInput";

interface Props {
  path: string;
}

function Matrix({ path }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Content>
        <MatrixInput study={study} url={path} computStats={MatrixStats.NOCOL} />
      </Content>
    </Root>
  );
}

export default Matrix;
