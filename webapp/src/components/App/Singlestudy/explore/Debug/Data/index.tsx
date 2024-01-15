import Text from "./Text";
import Json from "./Json";
import Matrix from "./Matrix";
import { FileType } from "../utils";

interface Props {
  studyId: string;
  fileType: FileType;
  filePath: string;
}

const componentByFileType = {
  matrix: Matrix,
  json: Json,
  file: Text,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const DataViewer = componentByFileType[fileType];

  return <DataViewer studyId={studyId} path={filePath} />;
}

export default Data;
