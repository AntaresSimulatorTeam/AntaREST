import Text from "./Text";
import Image from "./Image";
import Json from "./Json";
import Matrix from "./Matrix";
import type { FileInfo, FileType } from "../utils";

interface Props extends FileInfo {
  studyId: string;
}

interface DataComponentProps {
  studyId: string;
  path: string;
}
type DataComponent = React.ComponentType<DataComponentProps>;

const componentByFileType: Record<FileType, DataComponent> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  image: Image,
  folder: ({ path }) => path,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const DataViewer = componentByFileType[fileType];

  return <DataViewer studyId={studyId} path={filePath} />;
}

export default Data;
