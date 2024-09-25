import Text from "./Text";
import Image from "./Image";
import Json from "./Json";
import Matrix from "./Matrix";
import Folder from "./Folder";
import { canEditFile, type FileInfo, type FileType } from "../utils";
import type { DataCompProps } from "../utils";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import type { StudyMetadata } from "../../../../../../common/types";

interface Props extends FileInfo {
  study: StudyMetadata;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

type DataComponent = React.ComponentType<DataCompProps>;

const componentByFileType: Record<FileType, DataComponent> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  image: Image,
  folder: Folder,
} as const;

function Data(props: Props) {
  const { study, setSelectedFile, reloadTreeData, ...fileInfo } = props;
  const { fileType, filePath } = fileInfo;
  const canEdit = canEditFile(study, filePath);
  const DataViewer = componentByFileType[fileType];

  return (
    <ViewWrapper>
      <DataViewer
        {...fileInfo}
        studyId={study.id}
        canEdit={canEdit}
        setSelectedFile={setSelectedFile}
        reloadTreeData={reloadTreeData}
      />
    </ViewWrapper>
  );
}

export default Data;
