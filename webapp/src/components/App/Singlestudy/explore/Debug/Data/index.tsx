import Text from "./Text";
import Image from "./Image";
import Json from "./Json";
import Matrix from "./Matrix";
import Folder from "./Folder";
import type { FileInfo, FileType } from "../utils";
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
  const DataViewer = componentByFileType[fileType];

  const enableImport =
    !study.archived &&
    (filePath === "user" || filePath.startsWith("user/")) &&
    // To remove when Xpansion tool configuration will be moved to "input/expansion" directory
    !(filePath === "user/expansion" || filePath.startsWith("user/expansion/"));

  return (
    <ViewWrapper>
      <DataViewer
        {...fileInfo}
        studyId={study.id}
        enableImport={enableImport}
        setSelectedFile={setSelectedFile}
        reloadTreeData={reloadTreeData}
      />
    </ViewWrapper>
  );
}

export default Data;
