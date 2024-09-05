import Text from "./Text";
import Image from "./Image";
import Json from "./Json";
import Matrix from "./Matrix";
import type { FileInfo, FileType } from "../utils";
import type { DataCompProps } from "../utils";

interface Props extends FileInfo {
  studyId: string;
}

type DataComponent = React.ComponentType<DataCompProps>;

const componentByFileType: Record<FileType, DataComponent> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  image: Image,
  folder: ({ filePath }) => filePath,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const isUserFolder = filePath.startsWith("/user/");
  const DataViewer = componentByFileType[fileType];

  return (
    <DataViewer
      studyId={studyId}
      filePath={filePath}
      enableImport={isUserFolder}
    />
  );
}

export default Data;
